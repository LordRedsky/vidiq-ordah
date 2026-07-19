"""
core/youtube_service.py
========================
Integrasi YouTube Data API v3 untuk riset kompetitor
dan generasi 7 ide judul CTR tinggi menggunakan Gemini LLM.
"""

import os
import re
from collections import Counter
from dotenv import load_dotenv

load_dotenv(override=True)


def _get_youtube_api_key() -> str:
    import streamlit as st
    try:
        if hasattr(st, "secrets") and st.secrets:
            key = st.secrets.get("YOUTUBE_API_KEY") or st.secrets.get("API_KEY")
            if key and str(key).strip():
                return str(key).strip()
    except Exception:
        pass
    key = os.getenv("YOUTUBE_API_KEY") or os.getenv("API_KEY", "")
    return key.strip()


def _get_gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def get_youtube_client(api_key: str):
    from googleapiclient.discovery import build
    return build('youtube', 'v3', developerKey=api_key)


def riset_kompetitor(kata_kunci: str, max_results: int = 10) -> tuple[list[dict], list[str]]:
    """
    Menarik video kompetitor teratas dari YouTube dan mengekstrak tag/kata kunci.
    Returns: (videos_data, all_tags)
    """
    api_key = _get_youtube_api_key()
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY belum dikonfigurasi di .env")

    youtube = get_youtube_client(api_key)

    search_response = youtube.search().list(
        q=kata_kunci,
        type='video',
        part='snippet',
        maxResults=max_results,
        order='relevance'
    ).execute()

    video_ids = [
        item['id']['videoId']
        for item in search_response.get('items', [])
        if 'videoId' in item['id']
    ]

    if not video_ids:
        return [], []

    video_response = youtube.videos().list(
        id=','.join(video_ids),
        part='snippet,statistics'
    ).execute()

    videos_data = []
    all_tags = []

    for item in video_response.get('items', []):
        snippet = item.get('snippet', {})
        stats = item.get('statistics', {})
        tags = snippet.get('tags', [])
        all_tags.extend([t.lower() for t in tags])
        videos_data.append({
            "title": snippet.get('title', ''),
            "channel": snippet.get('channelTitle', ''),
            "views": int(stats.get('viewCount', 0)),
            "tags": tags,
            "url": f"https://www.youtube.com/watch?v={item.get('id', '')}"
        })

    return videos_data, all_tags


def generate_7_titles(topic: str, dna_text: str, competitor_data: list[dict], competitor_tags: list[str], prefer_groq: bool = False) -> list[dict]:
    """
    Menggunakan Gemini / Groq untuk menghasilkan 7 ide judul YouTube CTR tinggi
    berdasarkan topik, DNA Creator, dan data kompetitor YouTube.
    Returns: list of {"title": ..., "reason": ...}
    """
    tag_counter = Counter(competitor_tags)
    top_tags = [tag for tag, _ in tag_counter.most_common(15)]
    competitor_titles = "\n".join([f"- {v['title']} ({v['views']:,} views)" for v in competitor_data[:5]])

    prompt = f"""Kamu adalah seorang ahli strategi konten YouTube yang berpengalaman.

DNA KREATOR:
{dna_text[:3000]}

TOPIK VIDEO YANG INGIN DIBUAT:
{topic}

DATA KOMPETITOR (Judul & Views):
{competitor_titles if competitor_titles else 'Tidak ada data'}

TAG POPULER KOMPETITOR:
{', '.join(top_tags[:15]) if top_tags else 'Tidak ada'}

TUGAS:
Berikan TEPAT 7 ide judul YouTube terbaik yang:
1. Sesuai dengan karakter dan gaya DNA kreator di atas
2. Memiliki potensi CTR tinggi (clickbait edukatif, bukan clickbait murahan)
3. Relevan dengan topik dan audiens kreator
4. Menggunakan kata-kata kunci dari kompetitor yang relevan

Format output WAJIB seperti berikut (JSON array):
[
  {{"title": "Judul pertama di sini", "reason": "Alasan singkat mengapa CTR tinggi"}},
  {{"title": "Judul kedua di sini", "reason": "Alasan singkat"}},
  ...
]

Berikan HANYA JSON array, tanpa teks lain di luar JSON."""

    from core.llm_helper import call_llm_with_resilience

    raw = call_llm_with_resilience(
        prompt=prompt,
        temperature=0.7,
        max_output_tokens=4096,
        prefer_groq=prefer_groq
    )

    # Bersihkan markdown code block jika ada
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\s*```$', '', raw)

    import json
    try:
        titles = json.loads(raw)
        if isinstance(titles, list):
            return titles[:7]
    except Exception:
        pass

    # Fallback: parse manual
    lines = [l.strip() for l in raw.split('\n') if l.strip() and l.strip().startswith('"title"') or '"title"' in l]
    return [{"title": f"Judul {i+1} tentang {topic}", "reason": "Harap generate ulang"} for i in range(7)]
