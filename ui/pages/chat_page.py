"""
ui/pages/chat_page.py
Chat with Data — Fixed version.

Bugs fixed:
1. LLM sometimes returns plain text (not code) → show it directly
2. LLM returns code without fences → execute_safe handles it
3. Error message was swallowed — now always visible
4. chat_history key mismatch with app.py init
5. System prompt was too restrictive — relaxed to allow better answers
"""

from __future__ import annotations

import streamlit as st

from ai.prompt_builder import build_chat_system_prompt
from ai.safe_executor import execute_safe
from config.settings import CONFIG, get_groq_api_key


def _get_groq_client():
    api_key = get_groq_api_key()
    if not api_key:
        return None
    try:
        from groq import Groq  # noqa: PLC0415
        return Groq(api_key=api_key)
    except Exception:  # noqa: BLE001
        return None


def _call_llm(client, system_prompt: str, history: list[dict]) -> str:
    # Only keep last 10 messages to avoid token limit
    recent = history[-10:] if len(history) > 10 else history
    messages = [{"role": "system", "content": system_prompt}, *recent]
    response = client.chat.completions.create(
        model=CONFIG.ai.model,
        messages=messages,
        temperature=CONFIG.ai.temperature,
        max_tokens=CONFIG.ai.max_tokens,
    )
    return response.choices[0].message.content


def _is_code_response(text: str) -> bool:
    """Check if LLM returned Python code or plain text."""
    stripped = text.strip()
    return (
        "```python" in stripped
        or "```" in stripped
        or stripped.startswith("import ")
        or stripped.startswith("df")
        or stripped.startswith("fig")
        or stripped.startswith("print(")
        or stripped.startswith("result")
    )


def render() -> None:
    st.title("🗣️ Chat with your Data")
    st.caption("Ask questions in plain English — AI generates insights & charts.")

    load_result = st.session_state.get("load_result")
    profile = st.session_state.get("profile")
    clean_result = st.session_state.get("clean_result")

    if load_result is None or profile is None:
        st.warning("👈 Please upload a file first from the sidebar.")
        return

    # Use cleaned data if available
    df = clean_result.df if clean_result else load_result.df

    # ── API key check ─────────────────────────────────────────────
    client = _get_groq_client()
    if client is None:
        st.error("⚠️ **GROQ_API_KEY not configured.**")
        st.info(
            "Add your key to `.streamlit/secrets.toml`:\n"
            "```\nGROQ_API_KEY = 'gsk_your_key_here'\n```\n"
            "Get a free key at [console.groq.com](https://console.groq.com)"
        )
        return

    # ── Build system prompt ───────────────────────────────────────
    system_prompt = build_chat_system_prompt(df, profile)

    st.caption(
        f"Model: **{CONFIG.ai.model}** · "
        f"Data: **{'cleaned ✅' if clean_result else 'raw ⚠️'}** · "
        f"**{profile.total_rows:,}** rows · "
        f"**{profile.total_columns}** columns"
    )

    # ── Initialise chat history ───────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ── Suggested questions (only when empty) ─────────────────────
    if not st.session_state.chat_history:
        st.markdown("#### 💡 Try asking:")
        suggestions = []
        if profile.numeric_columns:
            suggestions.append(f"What is the average {profile.numeric_columns[0]}?")
            suggestions.append(f"Show distribution of {profile.numeric_columns[0]}")
        if profile.categorical_columns:
            suggestions.append(
                f"Show bar chart of {profile.categorical_columns[0]}"
            )
        suggestions.append("Which rows have the highest values?")
        suggestions.append("Summarise this dataset for me")
        suggestions = suggestions[:4]

        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            if cols[i % 2].button(s, key=f"sugg_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": s})
                st.rerun()

    # ── Render chat history ───────────────────────────────────────
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                if msg.get("output"):
                    st.markdown(msg["output"])
                if msg.get("figure"):
                    try:
                        st.plotly_chart(msg["figure"], use_container_width=True)
                    except Exception:  # noqa: BLE001
                        st.info("(Chart cannot be re-rendered — ask again to see it)")
                if msg.get("error"):
                    st.warning(msg["error"])
                if not msg.get("output") and not msg.get("figure") and not msg.get("error"):
                    st.markdown(msg.get("content", ""))
            else:
                st.markdown(msg["content"])

    # ── Chat input ────────────────────────────────────────────────
    user_input = st.chat_input(
        f"Ask anything about {load_result.file_name}...",
        key="chat_input",
    )

    if user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analysing your data..."):
                # ── Call LLM ─────────────────────────────────────
                try:
                    llm_history = [
                        {"role": m["role"], "content": m.get("content", "")}
                        for m in st.session_state.chat_history
                        if m.get("content")
                    ]
                    raw_response = _call_llm(client, system_prompt, llm_history)
                except Exception as e:  # noqa: BLE001
                    err = f"AI call failed: {type(e).__name__}: {e}"
                    st.error(err)
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": err,
                        "output": None, "figure": None, "error": err,
                    })
                    st.stop()

            assistant_msg = {
                "role": "assistant",
                "content": raw_response,
                "output": None,
                "figure": None,
                "error": None,
            }

            # ── Plain text answer (no code) ───────────────────────
            if not _is_code_response(raw_response):
                st.markdown(raw_response)
                assistant_msg["output"] = raw_response
                st.session_state.chat_history.append(assistant_msg)
                return

            # ── Execute sandboxed code ────────────────────────────
            with st.spinner("Running analysis..."):
                result = execute_safe(raw_response, df)

            if result.success:
                if result.output:
                    st.markdown(result.output)
                    assistant_msg["output"] = result.output
                if result.figure:
                    st.plotly_chart(result.figure, use_container_width=True)
                    assistant_msg["figure"] = result.figure
                if not result.output and not result.figure:
                    # Code ran but no output — show a helpful message
                    fallback = "Analysis complete. Try asking me to 'print' the result or 'show a chart'."
                    st.info(fallback)
                    assistant_msg["output"] = fallback

                # Debug expander
                with st.expander("🔍 View generated code"):
                    st.code(result.code_executed, language="python")
            else:
                # Execution failed — show error clearly
                st.warning(
                    f"I couldn't run that analysis: `{result.error}`\n\n"
                    "Try rephrasing your question."
                )
                assistant_msg["error"] = result.error
                with st.expander("🔍 View generated code"):
                    st.code(result.code_executed, language="python")

            st.session_state.chat_history.append(assistant_msg)

    # ── Clear button ──────────────────────────────────────────────
    if st.session_state.chat_history:
        st.divider()
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
