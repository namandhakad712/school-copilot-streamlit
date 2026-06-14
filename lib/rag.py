"""Keyword-based RAG retrieval over NCERT curriculum."""

import re
from .curriculum import CURRICULUM

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "do", "does", "did", "will", "would",
    "can", "could", "shall", "should", "may", "might", "must",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after",
    "and", "but", "or", "nor", "not", "so", "yet", "both",
    "either", "neither", "each", "every", "all", "any", "few",
    "more", "most", "other", "some", "such", "no", "only",
    "own", "same", "than", "too", "very", "just", "about",
    "samjhao", "samjhaiye", "explain", "batao", "bataye",
    "bacho", "dekho", "kya", "hai", "ek", "aur", "ko", "ka",
    "ki", "ke", "se", "mein", "par", "please", "tell", "about",
}


def extract_keywords(text: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9\s]", "", text.lower())
    words = cleaned.split()
    seen = set()
    result = []
    for w in words:
        if len(w) > 2 and w not in STOP_WORDS and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def retrieve_curriculum(query: str, max_results: int = 3) -> list[dict]:
    query_keywords = extract_keywords(query)
    if not query_keywords:
        return []

    scored = []
    for chunk in CURRICULUM:
        chunk_kws = chunk["keywords"]
        match_count = sum(
            1 for kw in chunk_kws
            if any(qk in kw or kw in qk for qk in query_keywords)
        )
        query_match_count = sum(
            1 for qk in query_keywords
            if any(kw in qk or qk in kw for kw in chunk_kws)
        )
        score = (
            (match_count / len(chunk_kws) + query_match_count / max(len(query_keywords), 1)) / 2
            if chunk_kws else 0
        )
        scored.append({"chunk": chunk, "score": score})

    scored = [s for s in scored if s["score"] > 0]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:max_results]


def format_curriculum_context(matches: list[dict]) -> str:
    if not matches:
        return ""
    sections = []
    for i, m in enumerate(matches):
        c = m["chunk"]
        sections.append(
            f"[CONTEXT {i+1}] Subject: {c['subject']} (Class {c['class_range']})\n"
            f"Chapter: {c['chapter']}\n"
            f"Topic: {c['topic']}\n"
            f"Reference: {c['content']}"
        )
    return f"\n--- Relevant Curriculum Context ---\n{''.join(sections)}\n--- End of Context ---\n"
