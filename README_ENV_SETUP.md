# ===========================================
# ENVIRONMENT SETUP
# ===========================================

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp env.example .env
   ```

2. **Fill in your actual API keys and secrets in `.env`:**
   - ClickUp API Token
   - Google Calendar credentials
   - OpenAI API Key
   - Hugging Face API Token
   - Other required credentials

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   cd app
   python wf.py
   ```

## Required API Keys

### ClickUp API
- Get your API token from: https://app.clickup.com/settings/apps
- Add your space ID from your ClickUp workspace

### Google Calendar API
- Create a project in Google Cloud Console
- Enable Google Calendar API
- Create OAuth 2.0 credentials
- Follow the setup wizard in the app

### OpenAI API
- Get your API key from: https://platform.openai.com/api-keys
- Used for AI-powered analysis and summaries

### Hugging Face API
- Get your token from: https://huggingface.co/settings/tokens
- Used for AI model inference

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secure and rotate them regularly
- Use environment variables for all sensitive data
- The `.env` file is already in `.gitignore`
