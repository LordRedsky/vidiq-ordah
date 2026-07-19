"""
core/exporter.py
================
Membuat file ZIP berstruktur dari semua aset scene:
  youtube/<job-title>/
    ├── gambar/   scene_01.png, scene_02.png, ...
    ├── voiceover/ scene_01.mp3, scene_02.mp3, ...
    └── video/    scene_01.mp4, scene_02.mp4, ... (jika ada)
"""

import os
import re
import zipfile
import shutil
import io
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
IMAGE_DIR = os.path.join(DATA_DIR, "images")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
VIDEO_DIR = os.path.join(DATA_DIR, "videos")
EXPORT_DIR = os.path.join(DATA_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def _safe_folder_name(title: str) -> str:
    """Membuat nama folder aman dari judul video."""
    safe = re.sub(r'[^\w\s-]', '', title).strip()
    safe = re.sub(r'\s+', '-', safe)
    safe = safe[:60]  # Batasi panjang nama folder
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{safe}_{timestamp}"


def create_export_zip(
    job_id: int,
    job_title: str,
    scenes: list[dict],
    include_images: bool = True,
    include_audio: bool = True,
    include_video: bool = True,
) -> bytes:
    """
    Membuat file ZIP berisi semua aset scene yang sudah digenerate.

    Args:
        job_id: ID job
        job_title: Judul video YouTube (untuk nama folder)
        scenes: list of scene dicts dari database
        include_images: Include file gambar
        include_audio: Include file voiceover
        include_video: Include file video

    Returns:
        bytes dari file ZIP (siap untuk st.download_button)
    """
    folder_name = _safe_folder_name(job_title)
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for scene in scenes:
            scene_num = scene.get('scene_number', 0)
            scene_str = f"scene_{scene_num:02d}"

            # ── Gambar ─────────────────────────────────────────────────────
            if include_images:
                img_path = scene.get('image_path') or get_default_image_path(job_id, scene_num)
                if img_path and os.path.exists(img_path):
                    ext = os.path.splitext(img_path)[1]
                    arc_name = f"youtube/{folder_name}/gambar/{scene_str}{ext}"
                    zf.write(img_path, arc_name)

            # ── Voiceover ──────────────────────────────────────────────────
            if include_audio:
                audio_path = scene.get('audio_path') or get_default_audio_path(job_id, scene_num)
                if audio_path and os.path.exists(audio_path):
                    ext = os.path.splitext(audio_path)[1]
                    arc_name = f"youtube/{folder_name}/voiceover/{scene_str}{ext}"
                    zf.write(audio_path, arc_name)

            # ── Video ──────────────────────────────────────────────────────
            if include_video:
                video_path = scene.get('video_path') or get_default_video_path(job_id, scene_num)
                if video_path and os.path.exists(video_path):
                    ext = os.path.splitext(video_path)[1]
                    arc_name = f"youtube/{folder_name}/video/{scene_str}{ext}"
                    zf.write(video_path, arc_name)

        # ── Tambahkan README.txt di dalam ZIP ─────────────────────────────
        readme_content = f"""Orchestra Dashboard - Export
============================
Video: {job_title}
Export: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Total Scenes: {len(scenes)}

Struktur Folder:
- gambar/    : Gambar per scene (scene_01.png, scene_02.png, ...)
- voiceover/ : Audio narasi per scene (scene_01.mp3, scene_02.mp3, ...)
- video/     : Video clip per scene (scene_01.mp4, scene_02.mp4, ...)

File sudah berurutan sesuai nomor scene.
Gabungkan menggunakan software editing video favorit Anda.
"""
        zf.writestr(f"youtube/{folder_name}/README.txt", readme_content)

    zip_buffer.seek(0)
    return zip_buffer.read()


def get_default_image_path(job_id: int, scene_number: int) -> str:
    return os.path.join(IMAGE_DIR, f"job{job_id:03d}_scene{scene_number:02d}.png")


def get_default_audio_path(job_id: int, scene_number: int) -> str:
    return os.path.join(AUDIO_DIR, f"job{job_id:03d}_scene{scene_number:02d}.mp3")


def get_default_video_path(job_id: int, scene_number: int) -> str:
    return os.path.join(VIDEO_DIR, f"job{job_id:03d}_scene{scene_number:02d}.mp4")


def get_export_stats(job_id: int, scenes: list[dict]) -> dict:
    """Hitung berapa banyak file yang tersedia untuk export."""
    image_count = sum(1 for s in scenes if os.path.exists(
        s.get('image_path') or get_default_image_path(job_id, s['scene_number'])
    ))
    audio_count = sum(1 for s in scenes if os.path.exists(
        s.get('audio_path') or get_default_audio_path(job_id, s['scene_number'])
    ))
    video_count = sum(1 for s in scenes if os.path.exists(
        s.get('video_path') or get_default_video_path(job_id, s['scene_number'])
    ))
    return {
        "total_scenes": len(scenes),
        "images_ready": image_count,
        "audio_ready": audio_count,
        "videos_ready": video_count,
    }
