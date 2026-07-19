"""
core/voiceover_service.py
==========================
Generator voiceover menggunakan edge-tts (Python, gratis).
Mendukung suara Bahasa Indonesia & Inggris secara alami.
"""

import asyncio
import os
import re

# Suara edge-tts yang tersedia
VOICE_OPTIONS = {
    "🇮🇩 Ardi (ID - Laki-laki)": "id-ID-ArdiNeural",
    "🇮🇩 Gadis (ID - Perempuan)": "id-ID-GadisNeural",
    "🇺🇸 Christopher (EN - Laki-laki)": "en-US-ChristopherNeural",
    "🇺🇸 Jenny (EN - Perempuan)": "en-US-JennyNeural",
    "🇺🇸 Guy (EN - Laki-laki Alt)": "en-US-GuyNeural",
    "🇬🇧 Ryan (UK - Laki-laki)": "en-GB-RyanNeural",
}

DEFAULT_VOICE = "id-ID-ArdiNeural"

# Folder output audio
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


async def _generate_audio_async(text: str, voice: str, output_path: str, rate: str = "+0%", volume: str = "+0%"):
    """Async internal function untuk generate audio."""
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await communicate.save(output_path)


def generate_voiceover(
    text: str,
    job_id: int,
    scene_number: int,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
) -> str:
    """
    Generate file audio MP3 dari teks narasi menggunakan edge-tts.

    Args:
        text: Teks narasi yang akan diubah jadi suara
        job_id: ID job (untuk penamaan file)
        scene_number: Nomor scene (untuk penamaan file)
        voice: Voice ID dari VOICE_OPTIONS
        rate: Kecepatan bicara (+10%, -5%, dst)

    Returns:
        Path file audio yang berhasil dibuat
    """
    # Bersihkan teks dari karakter yang tidak perlu
    clean_text = re.sub(r'\s+', ' ', text.strip())
    # Batasi teks jika terlalu panjang untuk satu scene (edge-tts limit)
    if len(clean_text) > 3000:
        clean_text = clean_text[:3000]

    filename = f"job{job_id:03d}_scene{scene_number:02d}.mp3"
    output_path = os.path.join(AUDIO_DIR, filename)

    # Jalankan async
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate_audio_async(clean_text, voice, output_path, rate))
        loop.close()
    except Exception as e:
        raise RuntimeError(f"Gagal generate voiceover scene {scene_number}: {str(e)}")

    return output_path


def generate_all_voiceovers(
    scenes: list[dict],
    job_id: int,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    progress_callback=None
) -> list[dict]:
    """
    Generate voiceover untuk semua scene sekaligus.

    Args:
        scenes: list of {scene_number, narasi, ...}
        job_id: ID job
        voice: Voice ID
        rate: Kecepatan bicara
        progress_callback: Fungsi callback(current, total) untuk update progress

    Returns:
        list of {scene_number, audio_path, status}
    """
    results = []
    total = len(scenes)

    for i, scene in enumerate(scenes):
        scene_num = scene.get('scene_number', i + 1)
        narasi = scene.get('narasi', '')

        if not narasi or narasi.strip() == '...':
            results.append({
                "scene_number": scene_num,
                "audio_path": None,
                "status": "skipped"
            })
            if progress_callback:
                progress_callback(i + 1, total)
            continue

        try:
            audio_path = generate_voiceover(narasi, job_id, scene_num, voice, rate)
            results.append({
                "scene_number": scene_num,
                "audio_path": audio_path,
                "status": "done"
            })
        except Exception as e:
            results.append({
                "scene_number": scene_num,
                "audio_path": None,
                "status": f"error: {str(e)[:100]}"
            })

        if progress_callback:
            progress_callback(i + 1, total)

    return results


def get_audio_path(job_id: int, scene_number: int) -> str:
    """Mendapatkan path audio untuk scene tertentu."""
    filename = f"job{job_id:03d}_scene{scene_number:02d}.mp3"
    return os.path.join(AUDIO_DIR, filename)


def audio_exists(job_id: int, scene_number: int) -> bool:
    """Cek apakah file audio sudah ada."""
    return os.path.exists(get_audio_path(job_id, scene_number))
