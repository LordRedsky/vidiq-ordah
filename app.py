import os
import re
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from collections import Counter

# Load environment variables
load_dotenv()

# --- YOUTUBE DATA API V3 FUNCTIONS ---
def get_youtube_client(api_key: str):
    from googleapiclient.discovery import build
    return build('youtube', 'v3', developerKey=api_key)

def riset_kompetitor_youtube(kata_kunci: str, api_key: str, max_results: int = 5) -> tuple[list[dict], list[str]]:
    """
    Menarik video kompetitor teratas dan ekstrak tag/kata kunci utama menggunakan YouTube Data API v3.
    """
    if not api_key:
        raise ValueError("YouTube API Key belum diisi di sidebar atau file .env")

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


# --- SCRIPT DOCTOR & RETENTION AUDIT ENGINE (PYTHON NLP/RULES) ---
def analisis_retensi_dan_seo(narasi: str, kata_kunci_utama: str, competitor_tags: list[str]) -> dict:
    """
    Menganalisis naskah narasi user berbasis logika audit retensi & perbandingan kata kunci YouTube API.
    """
    narasi_clean = narasi.strip()
    words = re.findall(r'\b\w+\b', narasi_clean.lower())
    total_words = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', narasi_clean) if len(s.strip()) > 3]
    
    # 1. Audit Kata Kunci (SEO)
    existing_keywords = set()
    recommended_keywords = set()
    
    # Check main keyword
    kw_words = set(re.findall(r'\b\w+\b', kata_kunci_utama.lower()))
    for w in kw_words:
        if w in words:
            existing_keywords.add(w)
            
    # Check competitor tags
    tag_counter = Counter(competitor_tags)
    top_competitor_keywords = [tag for tag, count in tag_counter.most_common(15) if len(tag) > 3]
    
    for tag in top_competitor_keywords:
        if tag in narasi_clean.lower() or any(w in words for w in tag.split()):
            existing_keywords.add(tag)
        else:
            recommended_keywords.add(tag)
            
    # 2. Audit Retensi & Kalimat Bertele-tele (Trimming Audit)
    kalimat_perlu_dihapus = []
    
    # Rules for filler phrases / slow intro
    filler_phrases = [
        ("kembali lagi bersama saya", "Intro terlalu umum dan lambat. Langsung masuk ke nilai utama (hook) video."),
        ("pada kesempatan kali ini", "Basa-basi intro yang berpotensi menurunkan audience retention di 10 detik pertama."),
        ("di video hari ini saya mau membahas", "Kalimat pasif bertele-tele. Ganti dengan klaim/pertanyaan pembuka yang kuat."),
        ("sebelum kita mulai jangan lupa", "Call-to-action (CTA) terlalu cepat di awal naskah membuat penonton skip."),
        ("jangan lupa klik tombol subscribe", "Minta subscribe di awal video terbukti menurunkan retensi awal penonton."),
        ("demikianlah tips dari saya hari ini", "Outro lambat yang memberi sinyal video sudah selesai sehingga penonton langsung menutup video."),
        ("terima kasih sudah menonton", "Outro penutup pasif. Sebaiknya gunakan End Screen Binge-watching trigger."),
        ("seperti yang kita tahu", "Pengulangan asumsi publik yang tidak menambah nilai poin naskah.")
    ]
    
    for phrase, alasan in filler_phrases:
        if phrase in narasi_clean.lower():
            # Find exact matching sentence in user text
            matched_sentence = next((s for s in sentences if phrase in s.lower()), phrase)
            kalimat_perlu_dihapus.append({
                "kalimat": matched_sentence,
                "alasan": alasan
            })
            
    # Check for extra long sentences (> 25 words)
    for s in sentences:
        s_words = re.findall(r'\b\w+\b', s)
        if len(s_words) > 28 and not any(k['kalimat'] == s for k in kalimat_perlu_dihapus):
            kalimat_perlu_dihapus.append({
                "kalimat": s,
                "alasan": f"Kalimat terlalu panjang ({len(s_words)} kata). Pisahkan menjadi kalimat pendek agar ritme voiceover lebih dinamis."
            })

    # 3. Hitung Skor SEO & Retensi (1-100)
    score = 75
    
    # Reward for keywords
    if len(existing_keywords) >= 3:
        score += 15
    elif len(existing_keywords) >= 1:
        score += 5
        
    # Penalty for retention issues
    score -= (len(kalimat_perlu_dihapus) * 7)
    
    # Word count check
    if total_words < 50:
        score -= 15
        
    score = max(20, min(98, score))
    
    # 4. Saran Optimasi Taktis
    saran = f"Naskah Anda terdiri dari {total_words} kata (~{round(total_words/130, 1)} menit voiceover). "
    if len(kalimat_perlu_dihapus) > 0:
        saran += f"Terdapat {len(kalimat_perlu_dihapus)} bagian bertele-tele yang perlu di-trim agar penonton tidak menutup video. "
    saran += f"Disarankan menyelipkan tag kata kunci tren kompetitor seperti: {', '.join(list(recommended_keywords)[:4])} ke dalam narasi."
    
    return {
        "skor_seo": score,
        "total_kata": total_words,
        "kata_kunci_ditemukan": list(existing_keywords)[:8],
        "rekomendasi_kata_kunci": list(recommended_keywords)[:8],
        "kalimat_perlu_dihapus": kalimat_perlu_dihapus,
        "saran_optimasi": saran
    }


# --- STREAMLIT USER INTERFACE ---
st.set_page_config(
    page_title="vidIQ AI Script Doctor & SEO Specialist",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #FF0000 0%, #B20710 40%, #1F1F1F 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(255, 0, 0, 0.15);
    }
    
    .score-card {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
    }
    
    .badge-existing {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        margin: 4px;
        font-weight: 600;
        font-size: 0.88rem;
    }
    
    .badge-recommended {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        margin: 4px;
        font-weight: 600;
        font-size: 0.88rem;
    }
    
    .trim-card {
        background: rgba(239, 68, 68, 0.05);
        border-left: 4px solid #EF4444;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .trim-text {
        font-weight: 600;
        color: #FCA5A5;
        font-size: 0.95rem;
    }
    
    .trim-reason {
        color: #D1D5DB;
        font-size: 0.9rem;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-weight: 800; font-size: 2.2rem;">🎬 vidIQ Script Doctor & YouTube SEO Specialist</h1>
    <p style="margin-top: 8px; opacity: 0.9; font-size: 1.05rem;">
        Audit retensi narasi & optimasi SEO naskah video YouTube menggunakan data tren dari <b>YouTube Data API v3</b>.
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Konfigurasi API")
    
    default_yt_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("API_KEY") or ""
    youtube_api_key = st.text_input("YouTube Data API Key", value=default_yt_key, type="password", help="Diperlukan untuk menarik data tren kompetitor")
    
    st.divider()
    st.markdown("### 📝 Contoh Naskah")
    if st.button("Isi Naskah Contoh (Demo)"):
        st.session_state["kata_kunci_input"] = "Cara Menambah Subscriber YouTube Fast 2026"
        st.session_state["narasi_input"] = """Halo semuanya, kembali lagi bersama saya di channel ini. Pada kesempatan kali ini, di video hari ini saya mau membahas sesuatu yang sangat menarik banget buat kalian semua yaitu tentang cara menambah subscriber YouTube dengan cepat di tahun 2026. Tapi sebelum kita mulai ke pembahasannya, jangan lupa klik tombol subscribe dan menyalakan lonceng notifikasinya ya guys biar tidak ketinggalan video terbaru dari saya.

Oke langsung saja, seperti yang kita tahu menaikkan subscriber itu sangat susah sekali kalau kita tidak tahu triknya. Banyak orang yang menyerah di tengah jalan. Pertama-tama kalian harus sering upload video YouTube Shorts. Shorts itu sangat bagus untuk mendorong jangkuan channel. Selain itu kalian juga perlu buat thumbnail yang bagus dan judul yang bikin penasaran.

Demikianlah tips dari saya hari ini, terima kasih sudah menonton sampai akhir, sampai jumpa di video selanjutnya bye bye!"""

# Inputs Section (Kotak Narasi User)
col_left, col_right = st.columns([1, 1])

with col_left:
    kata_kunci_utama = st.text_input(
        "🎯 Topik / Kata Kunci Utama Video",
        value=st.session_state.get("kata_kunci_input", ""),
        placeholder="Contoh: Cara Menambah Subscriber YouTube 2026"
    )

with col_right:
    st.caption("💡 Data tren kata kunci kompetitor akan ditarik otomatis via YouTube Data API v3.")

narasi_user = st.text_area(
    "📄 Narasi / Skrip Draf Video YouTube (Kotak Utama)",
    value=st.session_state.get("narasi_input", ""),
    height=280,
    placeholder="Paste narasi atau naskah voiceover video Anda di sini untuk di-audit..."
)

btn_analisis = st.button("🚀 Jalankan Analisis Retensi & SEO Narasi", type="primary", use_container_width=True)

# Trigger Analysis Execution
if btn_analisis:
    if not youtube_api_key:
        st.error("❌ Silakan masukkan **YouTube Data API Key** di sidebar terlebih dahulu.")
    elif not kata_kunci_utama.strip():
        st.warning("⚠️ Masukkan topik atau kata kunci utama terlebih dahulu.")
    elif not narasi_user.strip():
        st.warning("⚠️ Masukkan narasi atau skrip yang ingin dianalisis.")
    else:
        with st.spinner("🔍 Menarik tren kompetitor dari YouTube Data API v3 & mengeksekusi Audit Retensi Script..."):
            try:
                # 1. Query YouTube API
                videos_kompetitor, competitor_tags = riset_kompetitor_youtube(kata_kunci_utama, youtube_api_key)
                
                # 2. Execute Script Audit Engine
                hasil = analisis_retensi_dan_seo(narasi_user, kata_kunci_utama, competitor_tags)
                
                st.session_state["hasil_analisis"] = hasil
                st.session_state["videos_kompetitor"] = videos_kompetitor
                st.success("✅ Audit narasi berhasil diproses!")
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan saat memproses data: {str(e)}")

# Display Results Dashboard
if "hasil_analisis" in st.session_state:
    hasil = st.session_state["hasil_analisis"]
    videos_kompetitor = st.session_state.get("videos_kompetitor", [])
    
    st.divider()
    st.subheader("📊 Hasil Audit Retensi Naskah & SEO YouTube")
    
    # Top Overview Metrics
    m1, m2, m3 = st.columns([1, 1, 2])
    
    with m1:
        score = hasil["skor_seo"]
        color_class = "#10B981" if score >= 80 else "#F59E0B" if score >= 60 else "#EF4444"
        st.markdown(f"""
        <div class="score-card">
            <h4 style="margin:0; color:#9CA3AF;">Skor Retensi & SEO</h4>
            <div style="font-size: 3.5rem; font-weight: 800; color: {color_class}; margin: 8px 0;">{score}<span style="font-size:1.5rem; color:#6B7280;">/100</span></div>
            <progress value="{score}" max="100" style="width: 100%;"></progress>
        </div>
        """, unsafe_allow_html=True)
        
    with m2:
        trim_count = len(hasil["kalimat_perlu_dihapus"])
        st.markdown(f"""
        <div class="score-card">
            <h4 style="margin:0; color:#9CA3AF;">Audit Retensi (Trim)</h4>
            <div style="font-size: 3.5rem; font-weight: 800; color: #EF4444; margin: 8px 0;">{trim_count}</div>
            <p style="margin:0; color:#D1D5DB; font-size:0.85rem;">Kalimat bertele-tele terdeteksi</p>
        </div>
        """, unsafe_allow_html=True)
        
    with m3:
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1F2937; border-radius:14px; padding:1.2rem; height:100%;">
            <h4 style="margin:0 0 8px 0; color:#9CA3AF;">💡 Ringkasan Script Doctor</h4>
            <p style="color:#E5E7EB; margin:0; line-height:1.5; font-size:0.95rem;">
                {hasil['saran_optimasi']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    
    # Detailed Tabs
    tab_trim, tab_keywords, tab_competitor, tab_json = st.tabs([
        "✂️ Audit Retensi (Kalimat Perlu Dihapus)",
        "🎯 Kata Kunci & SEO",
        "🔍 Tren Kompetitor YouTube",
        "📥 Raw JSON Output"
    ])

    with tab_trim:
        st.markdown("#### ✂️ Rekomendasi Kalimat Yang Disarankan DIHAPUS / DIUBAH Demi Retensi")
        trim_items = hasil.get("kalimat_perlu_dihapus", [])
        if trim_items:
            for idx, item in enumerate(trim_items, start=1):
                txt = item.get('kalimat', '')
                rsn = item.get('alasan', '')
                st.markdown(f"""
                <div class="trim-card">
                    <div class="trim-text">#{idx} "{txt}"</div>
                    <div class="trim-reason"><b>Alasan Retensi:</b> {rsn}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("🎉 Luar biasa! Naskah Anda bebas dari intro/outro bertele-tele.")
    
    with tab_keywords:
        c_k1, c_k2 = st.columns(2)
        with c_k1:
            st.markdown("#### ✅ Kata Kunci Ditemukan di Narasi Anda")
            found_keywords = hasil.get("kata_kunci_ditemukan", [])
            if found_keywords:
                html_found = "".join([f'<span class="badge-existing">✓ {kw}</span>' for kw in found_keywords])
                st.markdown(html_found, unsafe_allow_html=True)
            else:
                st.info("Belum ada kata kunci utama yang terdeteksi secara dominan.")
                
        with c_k2:
            st.markdown("#### ⚡ Rekomendasi Kata Kunci Tren Kompetitor")
            rec_keywords = hasil.get("rekomendasi_kata_kunci", [])
            if rec_keywords:
                html_rec = "".join([f'<span class="badge-recommended">+ {kw}</span>' for kw in rec_keywords])
                st.markdown(html_rec, unsafe_allow_html=True)
            else:
                st.success("Kepadatan kata kunci Anda sudah sangat optimal!")

    with tab_competitor:
        st.markdown("#### 🏆 Video Kompetitor Peringkat Atas (Referensi Algoritma YouTube)")
        if videos_kompetitor:
            for v in videos_kompetitor:
                st.markdown(f"- **[{v['title']}]({v['url']})** — *(Channel: {v['channel']} | Views: {v['views']:,})*")
        else:
            st.write("Tidak ada data video kompetitor.")

    with tab_json:
        st.markdown("#### 📄 Output Audit Terstruktur")
        raw_json_str = json.dumps(hasil, indent=2, ensure_ascii=False)
        st.code(raw_json_str, language="json")
        st.download_button(
            label="💾 Download Hasil Audit (JSON)",
            data=raw_json_str,
            file_name="audit_narasi_vidiq.json",
            mime="application/json"
        )
