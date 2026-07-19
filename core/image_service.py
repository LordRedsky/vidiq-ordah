"""
core/image_service.py
=====================
Generator gambar menggunakan Google Gemini Imagen / Nano Banana
via google-genai SDK.
"""

import os
import base64
import re
from dotenv import load_dotenv

load_dotenv(override=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
IMAGE_DIR = os.path.join(DATA_DIR, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)


def _get_gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def generate_scene_image(
    visual_prompt: str,
    job_id: int,
    scene_number: int,
    character_image_path: str = None,
) -> str:
    """
    Generate gambar untuk satu scene menggunakan Google Imagen (Gemini API).

    Args:
        visual_prompt: Deskripsi visual scene dalam Bahasa Inggris
        job_id: ID job
        scene_number: Nomor scene
        character_image_path: Path gambar Main Character (opsional, untuk referensi)

    Returns:
        Path file gambar yang berhasil disimpan (PNG)
    """
    from google import genai
    from google.genai import types

    api_key = _get_gemini_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY belum dikonfigurasi di .env")

    client = genai.Client(api_key=api_key)

    # Sanitasi prompt: hilangkan kata negatif yang umum gagal di policy
    safe_prompt = _sanitize_prompt(visual_prompt)

    filename = f"job{job_id:03d}_scene{scene_number:02d}.png"
    output_path = os.path.join(IMAGE_DIR, filename)

    # Coba generate dengan Imagen 3
    try:
        from google import genai
        from google.genai import types
        api_key = _get_gemini_key()
        if api_key:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=safe_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    safety_filter_level="BLOCK_ONLY_HIGH",
                    person_generation="ALLOW_ADULT",
                )
            )
            if response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                return output_path
    except Exception as imagen_error:
        print(f"[Image Service] Imagen 3 gagal: {imagen_error}. Memakai Pollinations AI Flux...")

    # Fallback 1: Pollinations AI (Gratis, Flux HD 16:9, Tanpa API Key)
    try:
        import urllib.parse
        import urllib.request
        encoded_prompt = urllib.parse.quote(safe_prompt)
        poll_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={job_id*100 + scene_number}"
        req = urllib.request.Request(poll_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if data and len(data) > 5000:
                with open(output_path, "wb") as f:
                    f.write(data)
                return output_path
    except Exception as poll_err:
        print(f"[Image Service] Pollinations AI gagal: {poll_err}")

    # Fallback 2: generate placeholder dengan informasi scene
    _create_placeholder_image(output_path, scene_number, visual_prompt)
    return output_path


def _sanitize_prompt(prompt: str) -> str:
    """Membersihkan prompt dari kata-kata yang mungkin melanggar content policy."""
    # Hapus kata-kata yang berpotensi di-flag
    forbidden = ['violence', 'blood', 'gore', 'nude', 'naked', 'sexual', 'weapon', 'gun']
    cleaned = prompt
    for word in forbidden:
        cleaned = re.sub(word, '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _create_placeholder_image(output_path: str, scene_number: int, prompt: str):
    """Buat gambar placeholder saat API image generation gagal."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        # Buat gambar 1920x1080 dengan latar gelap
        img = Image.new('RGB', (1920, 1080), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Gradien sederhana
        for y in range(1080):
            alpha = int(255 * (1 - y / 1080) * 0.3)
            draw.line([(0, y), (1920, y)], fill=(30 + alpha//10, 50 + alpha//10, 80 + alpha//10))

        # Teks scene number
        draw.text((960, 400), f"Scene {scene_number}", fill=(148, 163, 184), anchor="mm",
                  font=None)

        # Prompt text (wrap)
        wrapped = textwrap.fill(prompt[:200], width=80)
        lines = wrapped.split('\n')
        y_start = 500
        for line in lines[:5]:
            draw.text((960, y_start), line, fill=(71, 85, 105), anchor="mm", font=None)
            y_start += 30

        img.save(output_path, "PNG")
    except Exception:
        # Jika PIL pun gagal, buat file kosong
        with open(output_path, 'wb') as f:
            # Minimal valid 1x1 PNG
            f.write(base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            ))


def get_image_path(job_id: int, scene_number: int) -> str:
    filename = f"job{job_id:03d}_scene{scene_number:02d}.png"
    return os.path.join(IMAGE_DIR, filename)


def image_exists(job_id: int, scene_number: int) -> bool:
    return os.path.exists(get_image_path(job_id, scene_number))
