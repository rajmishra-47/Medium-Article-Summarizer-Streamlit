import os

import streamlit as st
from dotenv import load_dotenv

from summarizer import (
    summarize_medium_article,
    summarize_with_openai,
    validate_medium_url,
)


load_dotenv()

st.set_page_config(page_title="Medium Article Summarizer", page_icon="📝", layout="wide")

st.title("Medium Article Summarizer")
st.write(
    "Paste a Medium article URL and get a concise summary of the article in seconds."
)

with st.sidebar:
    st.header("Settings")
    sentence_count = st.slider("Summary length (sentences)", min_value=3, max_value=12, value=6)
    use_openai = st.toggle("Use OpenAI (if OPENAI_API_KEY exists)", value=False)

url = st.text_input("Medium article URL", placeholder="https://medium.com/... or https://<publication>.medium.com/...")

if st.button("Summarize", type="primary"):
    if not url.strip():
        st.warning("Please enter a Medium article URL.")
        st.stop()

    if not validate_medium_url(url):
        st.error("Please provide a valid Medium URL.")
        st.stop()

    with st.spinner("Fetching and summarizing article..."):
        try:
            result = summarize_medium_article(url=url, sentence_count=sentence_count)

            st.subheader(result["title"] or "Article")
            st.caption(f"Estimated source length: {result['word_count']} words")

            summary = result["summary"]
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if use_openai and api_key:
                summary = summarize_with_openai(
                    text=result["article_text"],
                    api_key=api_key,
                )
            elif use_openai and not api_key:
                st.info("OPENAI_API_KEY is not set. Showing local summary instead.")

            st.markdown("### Summary")
            st.write(summary)

            with st.expander("View extracted article text"):
                st.write(result["article_text"])

        except Exception as exc:
            st.error(f"Could not summarize this article: {exc}")

st.markdown("---")
st.caption("Security note: API keys are read from environment variables and never hardcoded.")
