"""
core/scene_splitter.py
======================
Engine pemecah naskah YouTube menjadi 45 scene.
Setiap scene berisi:
- scene_number: nomor urut (1-45)
- narasi: potongan teks narasi
- visual_prompt: prompt gambar/video yang siap digunakan ke AI image generator
"""

import os
import re
import json
from dotenv import load_dotenv

load_dotenv(override=True)

TARGET_SCENES = 45


def _get_gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def split_script_to_scenes(
    script: str,
    title: str,
    dna_text: str,
    visual_style: str = "Photorealistic",
    character_description: str = "",
    prefer_groq: bool = False
) -> list[dict]:
    """
    Memecah naskah menjadi 45 scene menggunakan Gemini / Groq.
    Setiap scene memiliki narasi dan visual_prompt otomatis.

    Returns: list of {scene_number, narasi, visual_prompt}
    """
    gemini_key = _get_gemini_key()

    # Panduan style visual
    style_guides = {
        "Photorealistic": "Cinematic, lifelike, premium stock footage feel. High detail, realistic lighting, professional photography.",
        "Pencil Sketch": "Hand-drawn illustration, detailed pencil sketch style, clean lines, artistic crosshatching.",
        "Cartoon": "Bold, expressive cartoon illustration, vibrant colors, YouTube animation channel style.",
        "Infographic": "Clean data visualization, flat design, charts, icons, minimal text overlays, professional infographic.",
    }
    style_desc = style_guides.get(visual_style, style_guides["Photorealistic"])

    char_note = ""
    if character_description:
        char_note = f"""
KARAKTER UTAMA (WAJIB muncul di setiap scene yang relevan):
{character_description}
Konsistensi karakter WAJIB dijaga di semua visual prompt."""

    prompt = f"""Kamu adalah sutradara video YouTube yang berpengalaman.

JUDUL VIDEO: {title}
VISUAL STYLE: {visual_style} - {style_desc}
{char_note}

NASKAH YANG HARUS DIPECAH:
{script}

TUGAS:
Pecah naskah di atas menjadi TEPAT {TARGET_SCENES} scene yang mengalir secara logis dan sinematik.

Untuk setiap scene:
1. NARASI: Potongan teks narasi yang diucapkan (dari naskah asli, jangan diubah)
2. VISUAL_PROMPT: Deskripsi gambar/video yang menggambarkan scene tersebut dalam Bahasa Inggris, spesifik, detail, siap digunakan sebagai prompt untuk AI image generator.

Aturan VISUAL_PROMPT:
- Selalu dalam Bahasa Inggris
- Format: "Single continuous image, ONE frame only. [deskripsi scene]. {style_desc}. [detail karakter jika ada]. [detail latar/suasana]. [pencahayaan]"
- Spesifik tentang subjek, latar, mood, lighting, dan komposisi
- Jangan gunakan kata-kata negatif

Format output WAJIB JSON array:
[
  {{
    "scene_number": 1,
    "narasi": "Teks narasi scene pertama...",
    "visual_prompt": "Visual prompt dalam bahasa Inggris..."
  }},
  ...
]

Berikan HANYA JSON array, tanpa teks atau markdown di luar JSON.
WAJIB menghasilkan tepat {TARGET_SCENES} scene."""

    from core.llm_helper import call_llm_with_resilience

    raw = call_llm_with_resilience(
        prompt=prompt,
        temperature=0.7,
        max_output_tokens=8192,
        prefer_groq=prefer_groq
    )

    # Bersihkan markdown code block
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE | re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        scenes = json.loads(raw)
        if isinstance(scenes, list):
            # Pastikan ada scene_number yang benar
            for i, s in enumerate(scenes):
                s['scene_number'] = i + 1
            # Jika kurang dari 45, tambah scene kosong
            while len(scenes) < TARGET_SCENES:
                scenes.append({
                    "scene_number": len(scenes) + 1,
                    "narasi": "...",
                    "visual_prompt": f"A continuation scene from the video, {visual_style.lower()} style."
                })
            return scenes[:TARGET_SCENES]
    except Exception:
        pass

    # Fallback: bagi rata script ke 45 bagian
    return _fallback_split(script, visual_style, style_desc)


def _fallback_split(script: str, visual_style: str, style_desc: str) -> list[dict]:
    """Fallback jika parsing JSON gagal: bagi rata script ke 45 bagian."""
    paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]

    # Jika paragraf < 45, bagi per kalimat
    if len(paragraphs) < TARGET_SCENES:
        sentences = [s.strip() + '.' for s in re.split(r'(?<=[.!?])\s+', script) if len(s.strip()) > 10]
        paragraphs = sentences

    # Gabungkan atau bagi agar ada 45 chunks
    chunk_size = max(1, len(paragraphs) // TARGET_SCENES)
    chunks = []
    for i in range(0, len(paragraphs), chunk_size):
        chunk = ' '.join(paragraphs[i:i+chunk_size])
        if chunk:
            chunks.append(chunk)

    scenes = []
    for i in range(TARGET_SCENES):
        narasi = chunks[i] if i < len(chunks) else "..."
        scenes.append({
            "scene_number": i + 1,
            "narasi": narasi,
            "visual_prompt": f"Scene {i+1}: {narasi[:80]}... {style_desc}."
        })

    return scenes
