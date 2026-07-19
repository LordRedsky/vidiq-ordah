"""
core/script_doctor.py
=====================
vidIQ-style Script Doctor Engine:
- SEO Keyword Audit
- Retention / Trim Audit
- Skor SEO & Retensi
- Rekomendasi Optimasi
"""

import re
from collections import Counter


FILLER_PHRASES = [
    ("kembali lagi bersama saya", "Intro terlalu umum dan lambat. Langsung masuk ke nilai utama (hook) video."),
    ("pada kesempatan kali ini", "Basa-basi intro yang berpotensi menurunkan audience retention di 10 detik pertama."),
    ("di video hari ini saya mau membahas", "Kalimat pasif bertele-tele. Ganti dengan klaim/pertanyaan pembuka yang kuat."),
    ("sebelum kita mulai jangan lupa", "Call-to-action (CTA) terlalu cepat di awal naskah membuat penonton skip."),
    ("jangan lupa klik tombol subscribe", "Minta subscribe di awal video terbukti menurunkan retensi awal penonton."),
    ("demikianlah tips dari saya hari ini", "Outro lambat yang memberi sinyal video sudah selesai sehingga penonton menutup video."),
    ("terima kasih sudah menonton", "Outro penutup pasif. Sebaiknya gunakan End Screen Binge-watching trigger."),
    ("seperti yang kita tahu", "Pengulangan asumsi publik yang tidak menambah nilai poin naskah."),
    ("tidak perlu khawatir", "Kalimat negatif yang melemahkan urgensi konten."),
    ("oke langsung saja", "Transisi lemah yang tidak membangun antisipasi penonton."),
]


def analisis_retensi_dan_seo(narasi: str, kata_kunci_utama: str, competitor_tags: list[str]) -> dict:
    """
    Audit lengkap naskah narasi:
    - Deteksi filler phrases & kalimat bertele-tele
    - Audit kata kunci SEO vs kompetitor
    - Skor SEO & Retensi (0-100)
    - Saran optimasi
    """
    narasi_clean = narasi.strip()
    words = re.findall(r'\b\w+\b', narasi_clean.lower())
    total_words = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', narasi_clean) if len(s.strip()) > 5]

    # ── 1. Audit Kata Kunci SEO ──────────────────────────────────────────────
    existing_keywords = set()
    recommended_keywords = set()

    kw_words = set(re.findall(r'\b\w+\b', kata_kunci_utama.lower()))
    for w in kw_words:
        if w in words:
            existing_keywords.add(w)

    tag_counter = Counter(competitor_tags)
    top_competitor_keywords = [tag for tag, _ in tag_counter.most_common(20) if len(tag) > 3]

    for tag in top_competitor_keywords:
        tag_words = set(re.findall(r'\b\w+\b', tag.lower()))
        if tag.lower() in narasi_clean.lower() or any(w in words for w in tag_words):
            existing_keywords.add(tag)
        else:
            recommended_keywords.add(tag)

    # ── 2. Audit Retensi (Filler & Long Sentences) ──────────────────────────
    kalimat_perlu_dihapus = []

    for phrase, alasan in FILLER_PHRASES:
        if phrase in narasi_clean.lower():
            matched = next((s for s in sentences if phrase in s.lower()), phrase)
            kalimat_perlu_dihapus.append({
                "kalimat": matched[:200],
                "alasan": alasan,
                "tipe": "filler"
            })

    for s in sentences:
        s_words = re.findall(r'\b\w+\b', s)
        if len(s_words) > 30 and not any(k['kalimat'] in s for k in kalimat_perlu_dihapus):
            kalimat_perlu_dihapus.append({
                "kalimat": s[:200],
                "alasan": f"Kalimat terlalu panjang ({len(s_words)} kata). Pisahkan menjadi kalimat lebih pendek agar ritme voiceover lebih dinamis.",
                "tipe": "panjang"
            })

    # ── 3. Hitung Skor ───────────────────────────────────────────────────────
    score = 70
    if len(existing_keywords) >= 5:
        score += 20
    elif len(existing_keywords) >= 3:
        score += 12
    elif len(existing_keywords) >= 1:
        score += 5

    score -= len([k for k in kalimat_perlu_dihapus if k['tipe'] == 'filler']) * 8
    score -= len([k for k in kalimat_perlu_dihapus if k['tipe'] == 'panjang']) * 3

    if total_words < 100:
        score -= 20
    elif total_words > 1000:
        score += 5

    score = max(20, min(98, score))

    # ── 4. Saran Optimasi ────────────────────────────────────────────────────
    saran = f"Naskah terdiri dari {total_words:,} kata (~{round(total_words/130, 1)} menit voiceover). "
    filler_count = len([k for k in kalimat_perlu_dihapus if k['tipe'] == 'filler'])
    if filler_count > 0:
        saran += f"⚠️ Terdapat {filler_count} filler phrase yang disarankan dihapus untuk meningkatkan retensi. "
    rec_kw_list = list(recommended_keywords)[:5]
    if rec_kw_list:
        saran += f"💡 Sisipkan tag kompetitor berikut: {', '.join(rec_kw_list)}."

    return {
        "skor_seo": score,
        "total_kata": total_words,
        "total_karakter": len(narasi_clean),
        "kata_kunci_ditemukan": sorted(list(existing_keywords))[:10],
        "rekomendasi_kata_kunci": sorted(list(recommended_keywords))[:10],
        "kalimat_perlu_dihapus": kalimat_perlu_dihapus[:15],
        "saran_optimasi": saran,
    }
