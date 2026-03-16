# Medium Article Summarizer (Streamlit)

A Streamlit web app that takes a Medium article URL and generates a summary.

## Features

- Accepts Medium article links (`medium.com` and `*.medium.com`)
- Extracts article content
- Generates local extractive summaries (no API key required)
- Optional OpenAI-powered summary when `OPENAI_API_KEY` is set
- Keeps sensitive credentials in `.env`

## Setup

1. Create and activate a virtual environment (recommended)
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create environment file:

```bash
cp .env.example .env
```

4. (Optional) Add OpenAI API key in `.env`:

```env
OPENAI_API_KEY=your_key_here
```

## Run

```bash
streamlit run app.py
```

## Security

- Do not hardcode API keys in source code.
- `.env` is ignored via `.gitignore`.
- Use `.env.example` as a template for required variables.
