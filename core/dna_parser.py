"""
core/dna_parser.py
==================
Parser PDF DNA Creator menggunakan pypdf.
Mengekstraksi teks dari PDF, menyimpan ke SQLite,
dan mengelola upload file Main Character Image.
"""

import os
import shutil
from pypdf import PdfReader

# Folder penyimpanan asset upload
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DNA_ASSETS_DIR = os.path.join(DATA_DIR, "dna_assets")
os.makedirs(DNA_ASSETS_DIR, exist_ok=True)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Mengekstraksi seluruh teks dari file PDF DNA Creator.
    Returns teks gabungan dari semua halaman.
    """
    try:
        reader = PdfReader(pdf_path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text.strip())
        return "\n\n".join(pages_text)
    except Exception as e:
        raise ValueError(f"Gagal membaca PDF: {str(e)}")


def save_uploaded_pdf(uploaded_file, profile_name: str) -> str:
    """
    Menyimpan file PDF yang diupload via Streamlit ke folder data/dna_assets/.
    Returns path file yang disimpan.
    """
    safe_name = profile_name.strip().replace(" ", "_")
    filename = f"dna_{safe_name}.pdf"
    dest_path = os.path.join(DNA_ASSETS_DIR, filename)

    with open(dest_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return dest_path


def save_uploaded_character_image(uploaded_file, profile_name: str) -> str:
    """
    Menyimpan gambar Main Character yang diupload via Streamlit.
    Returns path file yang disimpan.
    """
    safe_name = profile_name.strip().replace(" ", "_")
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.webp']:
        ext = '.png'
    filename = f"char_{safe_name}{ext}"
    dest_path = os.path.join(DNA_ASSETS_DIR, filename)

    with open(dest_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return dest_path


def build_dna_system_prompt(dna_text: str, visual_style: str = "Photorealistic") -> str:
    """
    Membangun system prompt untuk LLM berdasarkan DNA Creator.
    Digunakan sebagai context awal untuk semua operasi generate.
    """
    return f"""Kamu adalah AI yang telah mempelajari karakter seorang kreator YouTube secara mendalam.
Berikut adalah DNA Kreator yang HARUS kamu patuhi sepenuhnya dalam setiap output:

=== DNA KREATOR ===
{dna_text}
===================

ATURAN WAJIB:
1. Gunakan gaya bahasa, pola berpikir, emosi, dan karakter yang sama persis dengan kreator di atas.
2. Jangan menggunakan gaya penulisan AI yang generik.
3. Pertahankan konsistensi karakter di setiap output tanpa terkecuali.
4. Gaya visual scene menggunakan style: {visual_style}

Kamu siap membantu kreator membuat konten YouTube yang terasa seperti dibuat langsung olehnya.
"""
