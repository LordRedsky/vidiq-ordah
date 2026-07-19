"""
core/script_generator.py
=========================
Generator naskah YouTube lengkap 10.000–11.000 karakter
menggunakan Gemini LLM, sesuai DNA Creator.
"""

import os
import re
from dotenv import load_dotenv

load_dotenv(override=True)


def _get_gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def generate_full_script(title: str, dna_text: str, visual_style: str = "Photorealistic", prefer_groq: bool = False) -> str:
    """
    Generate naskah YouTube lengkap 10.000–11.000 karakter sesuai DNA Creator.
    Struktur: Hook → Masalah → Insight Unik → Solusi → Studi Kasus → Penutup & CTA.
    Returns teks naskah mentah.
    """
    from core.llm_helper import call_llm_with_resilience

    system_instruction = f"""Kamu adalah kreator YouTube yang sedang menulis naskah video.
Kamu HARUS menulis persis seperti kreator berdasarkan DNA berikut:

=== DNA KREATOR ===
{dna_text[:4000]}
==================="""

    prompt = f"""JUDUL VIDEO: {title}
VISUAL STYLE: {visual_style}

TUGAS:
Tulis naskah YouTube LENGKAP dengan ketentuan ketat berikut:
- PANJANG WAJIB: antara 10.000 hingga 11.000 KARAKTER (bukan kata)
- Durasi target: 10-12 menit voiceover
- Gunakan gaya bahasa, energi, emosi, dan karakter PERSIS seperti kreator yang dianalisis
- JANGAN gunakan gaya penulisan AI generik
- JANGAN keluar dari karakter kreator

STRUKTUR WAJIB:
1. [HOOK] - Pembuka kuat yang langsung menyentuh emosi / rasa penasaran (1-2 paragraf)
2. [MASALAH] - Penjelasan masalah yang dihadapi audiens dari sudut pandang kreator
3. [INSIGHT UNIK] - Sudut pandang/insight yang berbeda dari kebanyakan orang
4. [SOLUSI] - Solusi dijelaskan secara runtut, dengan gaya kreator
5. [STUDI KASUS / CONTOH] - Contoh nyata atau studi kasus relevan
6. [PENUTUP & CTA] - Kesimpulan + call-to-action sesuai karakter kreator

PENTING:
- Tulis naskah secara MENGALIR seperti orang berbicara (bukan slide presentasi)
- Setelah selesai menulis, pastikan total karakter antara 10.000 - 11.000
- Mulai langsung dengan isi naskah, TANPA header seperti [HOOK] dll di dalam teks"""

    script = call_llm_with_resilience(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.85,
        max_output_tokens=8192,
        prefer_groq=prefer_groq
    )
    return script


def count_characters(text: str) -> int:
    """Hitung jumlah karakter dalam teks (termasuk spasi)."""
    return len(text)


def validate_script_length(script: str) -> dict:
    """Validasi panjang naskah dan kembalikan laporan."""
    char_count = count_characters(script)
    word_count = len(script.split())
    estimated_minutes = round(word_count / 130, 1)

    status = "✅ Optimal"
    if char_count < 9000:
        status = "⚠️ Terlalu pendek"
    elif char_count > 12000:
        status = "⚠️ Terlalu panjang"

    return {
        "char_count": char_count,
        "word_count": word_count,
        "estimated_minutes": estimated_minutes,
        "status": status,
        "in_range": 10000 <= char_count <= 11000,
    }
