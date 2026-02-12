# 🔑 Setting Up Your Groq API Key

## Option 1: For Local Development (Recommended)

1. Get your free API key from [Groq Cloud](https://console.groq.com/keys)
2. Open the file `.streamlit/secrets.toml` in this project
3. Replace `your_groq_api_key_here` with your actual API key:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```
4. Save the file and restart the Streamlit app

## Option 2: For Streamlit Cloud Deployment

1. Go to your app on [Streamlit Cloud](https://share.streamlit.io/)
2. Click on "Settings" → "Secrets"
3. Add the following:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```
4. Click "Save"

## Option 3: Manual Entry (Temporary)

If you don't want to save the key, you can enter it directly in the app interface when prompted.

---

**Note:** Never commit your `secrets.toml` file to Git. It's already added to `.gitignore` for your safety.
