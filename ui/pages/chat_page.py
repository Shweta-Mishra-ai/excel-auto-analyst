"""
ui/pages/chat_page.py
AI chat page — uses safe_executor (no raw exec!), full conversation history.
"""

from __future__ import annotations

import streamlit as st

from ai.prompt_builder import build_chat_system_prompt
from ai.safe_executor import execute_safe
from config.settings import CONFIG, get_groq_api_key


def _get_groq_client():
    """Return Groq client or None if key not configured."""
    api_key = get_groq_api_key()
    if not api_key:
        return None
    try:
        from groq import Groq

        return Groq(api_key=api_key)
    except ImportError:
        return None
    except Exception:
        return None


def _call_llm(client, system_prompt: str, history: list[dict]) -> str:
    """Call LLM and return the raw response string."""
    messages = [{"role": "system", "content": system_prompt}, *history]
    response = client.chat.completions.create(
        model=CONFIG.ai.model,
        messages=messages,
        temperature=CONFIG.ai.temperature,
        max_tokens=CONFIG.ai.max_tokens,
    )
    return response.choices[0].message.content


def render() -> None:
    st.header("💬 Chat with Your Data")

    load_result = st.session_state.load_result
    profile = st.session_state.profile
    clean_result = st.session_state.clean_result

    if profile is None:
        st.warning("Upload a file first.")
        return

    df = clean_result.df if clean_result else load_result.df
    client = _get_groq_client()

    if client is None:
        st.error(
            "**GROQ_API_KEY not configured.**\n\n"
            "Add it to `.streamlit/secrets.toml`:\n```\nGROQ_API_KEY = 'your_key_here'\n```\n"
            "Or set the environment variable `GROQ_API_KEY`."
        )
        return

    system_prompt = build_chat_system_prompt(df, profile)

    st.caption(
        f"Using **{CONFIG.ai.model}** · "
        f"Data: {'cleaned' if clean_result else 'raw'} · "
        f"{profile.total_rows:,} rows"
    )

    # ── Suggested questions ───────────────────────────────────────
    if not st.session_state.chat_history:
        st.subheader("Suggested Questions")
        suggestions = [
            f"What is the average of {profile.numeric_columns[0]}?"
            if profile.numeric_columns
            else None,
            f"Show a bar chart of {profile.categorical_columns[0]} distribution"
            if profile.categorical_columns
            else None,
            "Which rows have the highest values?",
            "Are there any unusual patterns in this data?",
        ]
        suggestions = [s for s in suggestions if s]

        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions[:4]):
            if cols[i % 2].button(suggestion, key=f"suggest_{i}"):
                st.session_state.chat_history.append(
                    {"role": "user", "content": suggestion}
                )
                st.rerun()

    # ── Chat history ──────────────────────────────────────────────
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                if message.get("output"):
                    st.write(message["output"])
                if message.get("figure"):
                    st.plotly_chart(message["figure"], use_container_width=True)
                if message.get("error"):
                    st.error(message["error"])
            else:
                st.write(message["content"])

    # ── Input ─────────────────────────────────────────────────────
    user_input = st.chat_input("Ask anything about your data...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Build message history for LLM (text only, no figures)
                    llm_history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history
                        if "content" in m
                    ]
                    raw_response = _call_llm(client, system_prompt, llm_history)
                except Exception as e:
                    st.error(f"LLM call failed: {type(e).__name__}: {e}")
                    return

            assistant_msg: dict = {
                "role": "assistant",
                "content": raw_response,
                "output": None,
                "figure": None,
                "error": None,
            }

            # Check if it's purely conversational text (no code fences and not parseable as code)
            import ast
            is_conversational = False
            if "```python" not in raw_response and "```" not in raw_response:
                try:
                    ast.parse(raw_response.strip())
                except SyntaxError:
                    is_conversational = True

            if is_conversational:
                st.write(raw_response)
                assistant_msg["output"] = raw_response
                st.session_state.chat_history.append(assistant_msg)
                return

            # ── Safe execution of generated code ──────────────────
            result = execute_safe(raw_response, df)

            if result.success:
                if result.output:
                    st.write(result.output)
                    assistant_msg["output"] = result.output
                if result.figure:
                    st.plotly_chart(result.figure, use_container_width=True)
                    assistant_msg["figure"] = result.figure
                if not result.output and not result.figure:
                    st.info("Code ran successfully but produced no visible output.")
            else:
                err_msg = f"Could not execute: {result.error}"
                st.error(err_msg)
                assistant_msg["error"] = err_msg

            st.session_state.chat_history.append(assistant_msg)

    # ── Clear history ─────────────────────────────────────────────
    if st.session_state.chat_history:
        if st.button("🗑️ Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()
