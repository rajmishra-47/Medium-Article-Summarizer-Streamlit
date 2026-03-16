import heapq
import re
from collections import Counter
from typing import Dict
from urllib.parse import urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in", "into", "is",
    "it", "no", "not", "of", "on", "or", "such", "that", "the", "their", "then", "there", "these",
    "they", "this", "to", "was", "will", "with", "you", "your", "we", "our", "from", "can", "have",
    "has", "had", "were", "been", "also", "about", "than", "what", "when", "where", "which", "who",
    "how", "why", "all", "any", "each", "few", "more", "most", "other", "some", "so", "too", "very",
}


def validate_medium_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.netloc.lower()
    return host == "medium.com" or host.endswith(".medium.com")


def _extract_with_bs4(html: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    article_tag = soup.find("article")
    if article_tag:
        paragraphs = [p.get_text(" ", strip=True) for p in article_tag.find_all("p")]
    else:
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]

    text = "\n\n".join([p for p in paragraphs if p])
    return {"title": title, "text": text}


def fetch_article(url: str) -> Dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    title = ""
    article_text = ""

    # Try direct page fetch first.
    try:
        response = requests.get(url, timeout=20, headers=headers)
        response.raise_for_status()
        fallback = _extract_with_bs4(response.text)
        title = fallback["title"]
        article_text = fallback["text"]
    except requests.RequestException:
        pass

    # Try trafilatura extraction as a stronger parser.
    downloaded = trafilatura.fetch_url(url)
    extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False) if downloaded else None
    if extracted and len(extracted.split()) > len(article_text.split()):
        article_text = extracted

    # Fallback for blocked pages (for example, 403/anti-bot responses).
    if len(article_text.split()) < 60:
        parsed = urlparse(url)
        no_scheme = f"{parsed.netloc}{parsed.path}"
        if parsed.query:
            no_scheme += f"?{parsed.query}"

        mirror_url = f"https://r.jina.ai/http://{no_scheme}"
        mirror_response = requests.get(mirror_url, timeout=25, headers=headers)
        mirror_response.raise_for_status()
        mirror_text = mirror_response.text.strip()
        if mirror_text:
            first_line = mirror_text.splitlines()[0].strip()
            if not title and first_line:
                title = first_line[:140]
            article_text = mirror_text

    if not article_text or len(article_text.split()) < 60:
        raise ValueError("Not enough article text could be extracted from this URL.")

    return {
        "title": title,
        "article_text": article_text.strip(),
    }


def _split_sentences(text: str):
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    return [s.strip() for s in sentences if len(s.strip().split()) > 4]


def summarize_text(text: str, sentence_count: int = 6) -> str:
    sentences = _split_sentences(text)
    if len(sentences) <= sentence_count:
        return " ".join(sentences)

    words = re.findall(r"[A-Za-z']+", text.lower())
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    if not words:
        return " ".join(sentences[:sentence_count])

    word_freq = Counter(words)
    max_freq = max(word_freq.values())
    for word in list(word_freq.keys()):
        word_freq[word] = word_freq[word] / max_freq

    sentence_scores = {}
    for sentence in sentences:
        sentence_words = re.findall(r"[A-Za-z']+", sentence.lower())
        sentence_scores[sentence] = sum(word_freq.get(w, 0) for w in sentence_words)

    top_sentences = heapq.nlargest(sentence_count, sentence_scores, key=sentence_scores.get)
    ordered_summary = [s for s in sentences if s in top_sentences]
    return " ".join(ordered_summary)


def summarize_with_openai(text: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    clipped_text = text[:12000]

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": "You summarize articles clearly and accurately.",
            },
            {
                "role": "user",
                "content": (
                    "Summarize the following Medium article in 8-10 concise bullet points. "
                    "Keep key claims, examples, and conclusions.\n\n"
                    f"ARTICLE:\n{clipped_text}"
                ),
            },
        ],
    )

    return response.output_text.strip()


def summarize_medium_article(url: str, sentence_count: int = 6) -> Dict[str, str]:
    article = fetch_article(url)
    summary = summarize_text(article["article_text"], sentence_count=sentence_count)
    return {
        "title": article["title"],
        "article_text": article["article_text"],
        "summary": summary,
        "word_count": len(article["article_text"].split()),
    }
