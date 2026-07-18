import os
import re
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from collections import Counter

# Load environment variables with override=True
load_dotenv(override=True)

# --- YOUTUBE DATA API V3 FUNCTIONS ---
def get_youtube_client(api_key: str):
    from googleapiclient.discovery import build
    return build('youtube', 'v3', developerKey=api_key)

def riset_kompetitor_youtube(kata_kunci: str, api_key: str, max_results: int = 5) -> tuple[list[dict], list[str]]:
    """
    Menarik video kompetitor teratas dan ekstrak tag/kata kunci utama menggunakan YouTube Data API v3.
    """
    if not api_key:
        raise ValueError("YouTube API Key belum terkonfigurasi di file .env (YOUTUBE_API_KEY)")

    youtube = get_youtube_client(api_key)
    
    # Search top videos
    search_response = youtube.search().list(
        q=kata_kunci,
        type='video',
        part='snippet',
        maxResults=max_results,
        order='relevance'
    ).execute()
    
    video_ids = [item['id']['videoId'] for item in search_response.get('items', []) if 'videoId' in item['id']]
    
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
        
        title = snippet.get('title', '')
        channel = snippet.get('channelTitle', '')
        tags = snippet.get('tags', [])
        view_count = int(stats.get('viewCount', 0))
        video_id = item.get('id', '')
        
        all_tags.extend([t.lower() for t in tags])
        
        videos_data.append({
            "title": title,
            "channel": channel,
            "views": view_count,
            "tags": tags,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })
        
    return videos_data, all_tags


# --- SCRIPT DOCTOR & RETENTION AUDIT ENGINE ---
def analisis_retensi_dan_seo(narasi: str, kata_kunci_utama: str, competitor_tags: list[str]) -> dict:
    narasi_clean = narasi.strip()
    words = re.findall(r'\b\w+\b', narasi_clean.lower())
    total_words = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', narasi_clean) if len(s.strip()) > 3]
    
    # 1. Audit Kata Kunci (SEO)
    existing_keywords = set()
    recommended_keywords = set()
    
    kw_words = set(re.findall(r'\b\w+\b', kata_kunci_utama.lower()))
    for w in kw_words:
        if w in words:
            existing_keywords.add(w)
            
    tag_counter = Counter(competitor_tags)
    top_competitor_keywords = [tag for tag, count in tag_counter.most_common(15) if len(tag) > 3]
    
    for tag in top_competitor_keywords:
        if tag in narasi_clean.lower() or any(w in words for w in tag.split()):
            existing_keywords.add(tag)
        else:
            recommended_keywords.add(tag)
            
    # 2. Audit Retensi (Trimming Audit)
    kalimat_perlu_dihapus = []
    
    filler_phrases = [
        ("kembali lagi bersama saya", "Intro terlalu umum dan lambat. Langsung masuk ke nilai utama (hook) video."),
        ("pada kesempatan kali ini", "Basa-basi intro yang berpotensi menurunkan audience retention di 10 detik pertama."),
        ("di video hari ini saya mau membahas", "Kalimat pasif bertele-tele. Ganti dengan klaim/pertanyaan pembuka yang kuat."),
        ("sebelum kita mulai jangan lupa", "Call-to-action (CTA) terlalu cepat di awal naskah membuat penonton skip."),
        ("jangan lupa klik tombol subscribe", "Minta subscribe di awal video terbukti menurunkan retensi awal penonton."),
        ("demikianlah tips dari saya hari ini", "Outro lambat yang memberi sinyal video sudah selesai sehingga penonton menutup video."),
        ("terima kasih sudah menonton", "Outro penutup pasif. Sebaiknya gunakan End Screen Binge-watching trigger."),
        ("seperti yang kita tahu", "Pengulangan asumsi publik yang tidak menambah nilai poin naskah.")
    ]
    
    for phrase, alasan in filler_phrases:
        if phrase in narasi_clean.lower():
            matched_sentence = next((s for s in sentences if phrase in s.lower()), phrase)
            kalimat_perlu_dihapus.append({
                "kalimat": matched_sentence,
                "alasan": alasan
            })
            
    for s in sentences:
        s_words = re.findall(r'\b\w+\b', s)
        if len(s_words) > 28 and not any(k['kalimat'] == s for k in kalimat_perlu_dihapus):
            kalimat_perlu_dihapus.append({
                "kalimat": s,
                "alasan": f"Kalimat terlalu panjang ({len(s_words)} kata). Pisahkan menjadi kalimat pendek agar ritme voiceover lebih dinamis."
            })

    # 3. Hitung Skor SEO & Retensi
    score = 75
    if len(existing_keywords) >= 3:
        score += 15
    elif len(existing_keywords) >= 1:
        score += 5
        
    score -= (len(kalimat_perlu_dihapus) * 7)
    if total_words < 50:
        score -= 15
        
    score = max(20, min(98, score))
    
    # 4. Saran Optimasi
    saran = f"Naskah terdiri dari {total_words} kata (~{round(total_words/130, 1)} menit voiceover). "
    if len(kalimat_perlu_dihapus) > 0:
        saran += f"Terdapat {len(kalimat_perlu_dihapus)} bagian bertele-tele yang disarankan di-trim. "
    saran += f"Disarankan menyelipkan tag kompetitor: {', '.join(list(recommended_keywords)[:4])}."
    
    return {
        "skor_seo": score,
        "total_kata": total_words,
        "kata_kunci_ditemukan": list(existing_keywords)[:8],
        "rekomendasi_kata_kunci": list(recommended_keywords)[:8],
        "kalimat_perlu_dihapus": kalimat_perlu_dihapus,
        "saran_optimasi": saran
    }


# --- STREAMLIT USER INTERFACE (COMPACT & SOFT VIDIQ PALETTE) ---
st.set_page_config(
    page_title="vidIQ Script Doctor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Soft vidIQ Design Tokens (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Compact Main Container */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px;
    }
    
    /* Soft vidIQ Header Bar */
    .vidiq-header {
        background: #0F172A;
        border: 1px solid #1E293B;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.25rem;
    }
    
    .vidiq-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin: 0;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .vidiq-badge-sub {
        background: #3B82F6;
        color: white;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Soft Compact Metric Cards */
    .metric-box {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    
    .metric-value-score {
        font-size: 2.4rem;
        font-weight: 800;
        margin: 4px 0;
    }
    
    .badge-soft-green {
        display: inline-block;
        background: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.25);
        padding: 4px 10px;
        border-radius: 6px;
        margin: 3px;
        font-weight: 500;
        font-size: 0.83rem;
    }
    
    .badge-soft-blue {
        display: inline-block;
        background: rgba(99, 102, 241, 0.12);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.25);
        padding: 4px 10px;
        border-radius: 6px;
        margin: 3px;
        font-weight: 500;
        font-size: 0.83rem;
    }
    
    .trim-card-soft {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-left: 3px solid #F87171;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.75rem;
    }
    
    .trim-txt {
        font-weight: 600;
        color: #FCA5A5;
        font-size: 0.9rem;
    }
    
    .trim-rsn {
        color: #94A3B8;
        font-size: 0.83rem;
        margin-top: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Compact Header
st.markdown("""
<div class="vidiq-header">
    <div class="vidiq-title">
        ⚡ vidIQ Script Doctor & SEO Audit
        <span class="vidiq-badge-sub">YouTube API v3</span>
    </div>
    <div style="font-size:0.85rem; color:#94A3B8;">
        Optimasi retensi & kata kunci secara otomatis
    </div>
</div>
""", unsafe_allow_html=True)

# Load API Key silently from environment
load_dotenv(override=True)
youtube_api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("API_KEY") or ""

# Inputs Form (Compact Layout)
c1, c2 = st.columns([2, 1])

with c1:
    kata_kunci_utama = st.text_input(
        "Topik / Kata Kunci Utama",
        value=st.session_state.get("kata_kunci_input", ""),
        placeholder="Contoh: Cara Menambah Subscriber YouTube Fast 2026"
    )

with c2:
    st.write("")
    st.write("")
    if st.button("✨ Load Naskah Demo", use_container_width=True):
        st.session_state["kata_kunci_input"] = "Cara Menambah Subscriber YouTube Fast 2026"
        st.session_state["narasi_input"] = """Halo semuanya, kembali lagi bersama saya di channel ini. Pada kesempatan kali ini, di video hari ini saya mau membahas sesuatu yang sangat menarik banget buat kalian semua yaitu tentang cara menambah subscriber YouTube dengan cepat di tahun 2026. Tapi sebelum kita mulai ke pembahasannya, jangan lupa klik tombol subscribe dan menyalakan lonceng notifikasinya ya guys biar tidak ketinggalan video terbaru dari saya.

Oke langsung saja, seperti yang kita tahu menaikkan subscriber itu sangat susah sekali kalau kita tidak tahu triknya. Banyak orang yang menyerah di tengah jalan. Pertama-tama kalian harus sering upload video YouTube Shorts. Shorts itu sangat bagus untuk mendorong jangkuan channel. Selain itu kalian juga perlu buat thumbnail yang bagus dan judul yang bikin penasaran.

Demikianlah tips dari saya hari ini, terima kasih sudah menonton sampai akhir, sampai jumpa di video selanjutnya bye bye!"""
        st.rerun()

narasi_user = st.text_area(
    "Narasi / Skrip Video YouTube",
    value=st.session_state.get("narasi_input", ""),
    height=200,
    placeholder="Tempelkan draf naskah narasi video di sini..."
)

btn_analisis = st.button("🚀 Audit Narasi Sekarang", type="primary", use_container_width=True)

# Process Audit
if btn_analisis:
    if not youtube_api_key:
        st.error("❌ `YOUTUBE_API_KEY` belum terkonfigurasi pada berkas `.env` server.")
    elif not kata_kunci_utama.strip():
        st.warning("⚠️ Masukkan topik atau kata kunci utama terlebih dahulu.")
    elif not narasi_user.strip():
        st.warning("⚠️ Masukkan teks narasi naskah terlebih dahulu.")
    else:
        with st.spinner("Mengambil tren YouTube & memproses audit retensi..."):
            try:
                videos_kompetitor, competitor_tags = riset_kompetitor_youtube(kata_kunci_utama, youtube_api_key)
                hasil = analisis_retensi_dan_seo(narasi_user, kata_kunci_utama, competitor_tags)
                
                st.session_state["hasil_analisis"] = hasil
                st.session_state["videos_kompetitor"] = videos_kompetitor
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {str(e)}")

# Display Compact Results Dashboard
if "hasil_analisis" in st.session_state:
    hasil = st.session_state["hasil_analisis"]
    videos_kompetitor = st.session_state.get("videos_kompetitor", [])
    
    st.write("")
    
    # 3 Compact Metric Cards
    col_m1, col_m2, col_m3 = st.columns([1, 1, 2])
    
    with col_m1:
        score = hasil["skor_seo"]
        score_color = "#34D399" if score >= 80 else "#FBBF24" if score >= 60 else "#F87171"
        st.markdown(f"""
        <div class="metric-box">
            <div style="font-size:0.8rem; color:#94A3B8; font-weight:600;">SKOR RETENSI & SEO</div>
            <div class="metric-value-score" style="color: {score_color};">{score}<span style="font-size:1.1rem; color:#64748B;">/100</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_m2:
        trim_count = len(hasil["kalimat_perlu_dihapus"])
        st.markdown(f"""
        <div class="metric-box">
            <div style="font-size:0.8rem; color:#94A3B8; font-weight:600;">BAGIAN PERLU DI-TRIM</div>
            <div class="metric-value-score" style="color: #F87171;">{trim_count}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_m3:
        st.markdown(f"""
        <div class="metric-box" style="text-align:left;">
            <div style="font-size:0.8rem; color:#94A3B8; font-weight:600; margin-bottom:4px;">💡 SARAN TAKTIS</div>
            <div style="font-size:0.85rem; color:#E2E8F0; line-height:1.4;">{hasil['saran_optimasi']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    
    # Compact Tabs
    tab_trim, tab_kw, tab_comp, tab_json = st.tabs([
        "✂️ Audit Retensi",
        "🎯 Kata Kunci",
        "🔍 Tren Competitor",
        "📥 Export JSON"
    ])

    with tab_trim:
        trim_items = hasil.get("kalimat_perlu_dihapus", [])
        if trim_items:
            for idx, item in enumerate(trim_items, start=1):
                txt = item.get('kalimat', '')
                rsn = item.get('alasan', '')
                st.markdown(f"""
                <div class="trim-card-soft">
                    <div class="trim-txt">#{idx} "{txt}"</div>
                    <div class="trim-rsn"><b>Alasan Retensi:</b> {rsn}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("🎉 Naskah Anda bebas dari intro/outro bertele-tele!")
            
    with tab_kw:
        k1, k2 = st.columns(2)
        with k1:
            st.markdown("##### ✅ Kata Kunci di Narasi")
            found_keywords = hasil.get("kata_kunci_ditemukan", [])
            if found_keywords:
                html_found = "".join([f'<span class="badge-soft-green">✓ {kw}</span>' for kw in found_keywords])
                st.markdown(html_found, unsafe_allow_html=True)
            else:
                st.info("Belum ada kata kunci utama terdeteksi.")
                
        with k2:
            st.markdown("##### ⚡ Rekomendasi Kata Kunci Tren")
            rec_keywords = hasil.get("rekomendasi_kata_kunci", [])
            if rec_keywords:
                html_rec = "".join([f'<span class="badge-soft-blue">+ {kw}</span>' for kw in rec_keywords])
                st.markdown(html_rec, unsafe_allow_html=True)
            else:
                st.success("Kata kunci naskah sudah sangat optimal!")

    with tab_comp:
        st.markdown("##### 🏆 Video Kompetitor (YouTube API v3)")
        if videos_kompetitor:
            for v in videos_kompetitor:
                st.markdown(f"- **[{v['title']}]({v['url']})** — *(Channel: {v['channel']} | Views: {v['views']:,})*")
        else:
            st.write("Tidak ada data video kompetitor.")

    with tab_json:
        raw_json = json.dumps(hasil, indent=2, ensure_ascii=False)
        st.code(raw_json, language="json")
        st.download_button(
            label="💾 Download Hasil (JSON)",
            data=raw_json,
            file_name="audit_narasi_vidiq.json",
            mime="application/json"
        )
