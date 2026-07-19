"""
app.py - Orchestra Dashboard
YouTube Content Generator (Streamlit)
======================================
Full pipeline: DNA Creator → Riset Judul → Generate Script → vidIQ Audit → 45 Scenes → Voiceover & Image → Export ZIP
"""

import os
import sys
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

# Tambah core ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Inisialisasi database
from core.db import init_db
init_db()

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Orchestra Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif;
    background-color: #0D1117;
    color: #E6EDF3;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #161B22; }
  ::-webkit-scrollbar-thumb { background: #30363D; border-radius: 3px; }

  /* Main container */
  .block-container {
    padding: 1.5rem 2rem 3rem !important;
    max-width: 1400px;
  }

  /* Hide default streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }

  /* ── Header Bar ── */
  .orchestra-header {
    background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
    border: 1px solid #30363D;
    border-radius: 14px;
    padding: 1.25rem 1.75rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
  }
  .orchestra-logo {
    font-size: 1.5rem;
    font-weight: 800;
    color: #F0F6FC;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .badge-pro {
    background: linear-gradient(135deg, #1F6FEB, #388BFD);
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  .header-sub {
    font-size: 0.82rem;
    color: #7D8590;
  }

  /* ── Section Cards ── */
  .section-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
  }
  .section-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: #7D8590;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.85rem;
  }

  /* ── Visual Style Cards ── */
  .style-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-top: 8px;
  }
  .style-card {
    background: #1C2128;
    border: 2px solid #30363D;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .style-card:hover {
    border-color: #388BFD;
    background: #1F2937;
  }
  .style-card.active {
    border-color: #1F6FEB;
    background: rgba(31, 111, 235, 0.08);
  }
  .style-card-title {
    font-weight: 600;
    font-size: 0.88rem;
    color: #E6EDF3;
  }
  .style-card-sub {
    font-size: 0.75rem;
    color: #7D8590;
    margin-top: 2px;
  }

  /* ── Title Cards ── */
  .title-card {
    background: #1C2128;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 0.9rem 1rem;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .title-card:hover { border-color: #388BFD; }
  .title-card.selected {
    border-color: #3FB950;
    background: rgba(63, 185, 80, 0.05);
  }
  .badge-pending {
    display: inline-block;
    background: rgba(125, 133, 144, 0.15);
    color: #7D8590;
    border: 1px solid #30363D;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
  }
  .badge-selected {
    display: inline-block;
    background: rgba(63, 185, 80, 0.15);
    color: #3FB950;
    border: 1px solid rgba(63, 185, 80, 0.3);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
  }

  /* ── Metric Box ── */
  .metric-box {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
  }
  .metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 4px 0;
  }
  .metric-label {
    font-size: 0.72rem;
    color: #7D8590;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }

  /* ── Keyword Badges ── */
  .badge-green {
    display: inline-block;
    background: rgba(63, 185, 80, 0.1);
    color: #3FB950;
    border: 1px solid rgba(63, 185, 80, 0.25);
    padding: 3px 10px;
    border-radius: 20px;
    margin: 3px;
    font-size: 0.78rem;
    font-weight: 500;
  }
  .badge-blue {
    display: inline-block;
    background: rgba(56, 139, 253, 0.1);
    color: #79C0FF;
    border: 1px solid rgba(56, 139, 253, 0.25);
    padding: 3px 10px;
    border-radius: 20px;
    margin: 3px;
    font-size: 0.78rem;
    font-weight: 500;
  }

  /* ── Trim Card ── */
  .trim-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-left: 3px solid #F85149;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 8px;
  }
  .trim-text { color: #FFA198; font-weight: 600; font-size: 0.85rem; }
  .trim-reason { color: #7D8590; font-size: 0.78rem; margin-top: 3px; }

  /* ── Scene Card ── */
  .scene-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 10px;
    transition: border-color 0.2s;
  }
  .scene-card:hover { border-color: #388BFD; }
  .scene-card.done { border-left: 3px solid #3FB950; }
  .scene-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  .scene-num {
    font-weight: 700;
    color: #79C0FF;
    font-size: 0.88rem;
  }
  .scene-status-done {
    background: rgba(63, 185, 80, 0.1);
    color: #3FB950;
    border: 1px solid rgba(63, 185, 80, 0.3);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
  }
  .scene-status-pending {
    background: rgba(125, 133, 144, 0.1);
    color: #7D8590;
    border: 1px solid #30363D;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
  }
  .field-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #7D8590;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 4px;
  }
  .narasi-box {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 0.6rem 0.85rem;
    font-size: 0.85rem;
    color: #E6EDF3;
    line-height: 1.6;
    margin-bottom: 8px;
    max-height: 100px;
    overflow-y: auto;
  }
  .prompt-box {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 0.6rem 0.85rem;
    font-size: 0.78rem;
    color: #7D8590;
    font-style: italic;
    line-height: 1.5;
    max-height: 80px;
    overflow-y: auto;
  }

  /* ── Divider ── */
  .divider {
    border: none;
    border-top: 1px solid #21262D;
    margin: 1.25rem 0;
  }

  /* ── Streamlit overrides ── */
  .stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #0D1117 !important;
    border: 1px solid #30363D !important;
    color: #E6EDF3 !important;
    border-radius: 8px !important;
  }
  .stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
  }
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1F6FEB, #388BFD) !important;
    border: none !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(31,111,235,0.3) !important;
  }
  .stProgress > div > div > div {
    background: linear-gradient(90deg, #1F6FEB, #3FB950) !important;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #7D8590 !important;
    font-weight: 500 !important;
  }
  .stTabs [aria-selected="true"] {
    color: #E6EDF3 !important;
    border-bottom: 2px solid #1F6FEB !important;
  }
</style>
""", unsafe_allow_html=True)


# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def ss(key, default=None):
    """Shorthand untuk st.session_state.get."""
    return st.session_state.get(key, default)


def set_ss(**kwargs):
    for k, v in kwargs.items():
        st.session_state[k] = v


# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="orchestra-header">
  <div class="orchestra-logo">
    🎬 Orchestra Dashboard
    <span class="badge-pro">YouTube AI</span>
  </div>
  <div class="header-sub">DNA Creator → Script → 45 Scenes → Voiceover & Image</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR: DNA Creator Management
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🧬 DNA Creator")
    st.markdown("---")

    from core.db import (
        get_all_dna_profiles, create_dna_profile, get_dna_profile, update_dna_profile
    )
    from core.dna_parser import extract_text_from_pdf, save_uploaded_pdf, save_uploaded_character_image

    profiles = get_all_dna_profiles()
    profile_options = {f"{p['id']} — {p['name']}": p['id'] for p in profiles}

    with st.expander("➕ Upload DNA Creator Baru", expanded=len(profiles) == 0):
        dna_name = st.text_input("Nama Kreator", placeholder="Contoh: Raditya Dika")
        dna_pdf = st.file_uploader("Upload PDF DNA Creator", type=['pdf'])
        dna_char = st.file_uploader("Upload Main Character Image", type=['png', 'jpg', 'jpeg', 'webp'])

        if st.button("💾 Simpan DNA Creator", use_container_width=True):
            if not dna_name.strip():
                st.error("Nama kreator wajib diisi!")
            elif not dna_pdf:
                st.error("Upload PDF DNA Creator terlebih dahulu!")
            else:
                with st.spinner("Membaca PDF & menyimpan DNA..."):
                    try:
                        pdf_path = save_uploaded_pdf(dna_pdf, dna_name)
                        dna_text = extract_text_from_pdf(pdf_path)
                        char_path = None
                        if dna_char:
                            char_path = save_uploaded_character_image(dna_char, dna_name)
                        pid = create_dna_profile(dna_name, pdf_path, char_path, dna_text)
                        st.success(f"✅ DNA '{dna_name}' berhasil disimpan! (ID: {pid})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    st.markdown("---")
    st.markdown("**Pilih DNA Aktif**")
    if profiles:
        selected_profile_label = st.selectbox(
            "DNA Creator",
            options=list(profile_options.keys()),
            label_visibility="collapsed"
        )
        active_dna_id = profile_options[selected_profile_label]
        set_ss(active_dna_id=active_dna_id)

        active_profile = get_dna_profile(active_dna_id)
        if active_profile:
            st.markdown(f"<div style='font-size:0.78rem; color:#7D8590;'>📄 {os.path.basename(active_profile.get('pdf_path','') or 'Belum ada PDF')}</div>", unsafe_allow_html=True)
            if active_profile.get('character_image_path') and os.path.exists(active_profile['character_image_path']):
                st.image(active_profile['character_image_path'], caption="Main Character", use_container_width=True)
    else:
        st.info("Belum ada DNA Creator. Upload terlebih dahulu.")
        active_dna_id = None
        set_ss(active_dna_id=None)

    st.markdown("---")
    st.markdown("**🤖 LLM Script Engine**")
    llm_choice = st.radio(
        "LLM Engine",
        ["⚡ Auto (Gemini + Groq Failover)", "🚀 Groq (Llama 3.3 70B)", "💎 Gemini API"],
        index=0,
        label_visibility="collapsed"
    )
    set_ss(prefer_groq=("Groq" in llm_choice))

    with st.expander("⚙️ Anti-Rate Limit / Extra Keys", expanded=False):
        st.markdown("<div style='font-size:0.75rem; color:#7D8590;'>Key yang digunakan saat ini:</div>", unsafe_allow_html=True)
        extra_k2 = st.text_input("Gemini API Key #2", type="password", value=os.getenv("GEMINI_API_KEY_2", ""))
        extra_groq = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))

        if st.button("💾 Simpan Key Extra", use_container_width=True):
            if extra_k2:
                os.environ["GEMINI_API_KEY_2"] = extra_k2.strip()
            if extra_groq:
                os.environ["GROQ_API_KEY"] = extra_groq.strip()
            st.success("✅ API Keys tersimpan!")

    st.markdown("""
    <div style="font-size:0.72rem; color:#7D8590; text-align:center; margin-top:10px;">
    🎙️ Voiceover: edge-tts<br>
    🖼️ Image: Google Imagen 3<br>
    🤖 Script: Gemini + Groq Resilient
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ═══════════════════════════════════════════════════════════════════════════════

active_dna_id = ss('active_dna_id')
active_dna = get_dna_profile(active_dna_id) if active_dna_id else None

if not active_dna:
    st.info("👈 Silakan upload & pilih DNA Creator di sidebar untuk memulai.")
    st.stop()

dna_text = active_dna.get('dna_text', '')
char_image_path = active_dna.get('character_image_path')

# ─── SECTION 1: JOB RESUME & SETUP ──────────────────────────────────────────
from core.db import (
    get_all_jobs, create_job, get_job, get_title_candidates, save_title_candidates,
    select_title, get_selected_title, get_script, save_script, update_script_content,
    get_scenes, save_scenes, update_scene, get_scenes_summary
)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🎯 Setup Video</div>', unsafe_allow_html=True)

col_resume, col_new = st.columns([2, 1])

with col_resume:
    all_jobs = get_all_jobs()
    if all_jobs:
        job_options = {"— Buat Job Baru —": None}
        for j in all_jobs:
            label = f"{j['topic'][:50]} — {j['created_at'][:10]} ({j.get('dna_name','')[:20]})"
            job_options[label] = j['id']

        selected_label = st.selectbox(
            "Lanjutkan job sebelumnya",
            options=list(job_options.keys()),
            index=0
        )
        resumed_job_id = job_options[selected_label]

        if resumed_job_id and ss('current_job_id') != resumed_job_id:
            set_ss(current_job_id=resumed_job_id)
            st.rerun()
    else:
        st.markdown("<div style='color:#7D8590; font-size:0.85rem;'>Belum ada job sebelumnya.</div>", unsafe_allow_html=True)

current_job_id = ss('current_job_id')

with col_new:
    if st.button("🆕 Reset / Job Baru", use_container_width=True):
        for key in ['current_job_id', 'titles', 'audit_result', 'competitor_tags']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


# ─── SECTION 2: INPUT TOPIK & VISUAL STYLE ───────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📝 Topik & Visual Style</div>', unsafe_allow_html=True)

topic_input = st.text_input(
    "Topik Video",
    value=ss('topic_input', ''),
    placeholder="Masukkan topik video...",
    label_visibility="collapsed"
)

st.markdown("<div style='font-size:0.85rem; color:#7D8590; margin: 8px 0 6px;'>Visual Style</div>", unsafe_allow_html=True)

VISUAL_STYLES = {
    "Photorealistic": ("🎬", "Cinematic, lifelike — premium stock footage feel"),
    "Pencil Sketch":  ("✏️", "Hand-drawn illustration — Good Wisdom Daily style"),
    "Cartoon":        ("🎨", "Bold, expressive — Marth Finance style"),
    "Infographic":    ("📊", "Clean data viz — charts and numbers focused"),
}

current_style = ss('visual_style', 'Cartoon')

style_cols = st.columns(2)
for i, (style_name, (icon, desc)) in enumerate(VISUAL_STYLES.items()):
    with style_cols[i % 2]:
        is_active = current_style == style_name
        active_class = "active" if is_active else ""
        st.markdown(f"""
        <div class="style-card {active_class}" onclick="">
          <div class="style-card-title">{icon} {style_name}</div>
          <div class="style-card-sub">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"{'✅ ' if is_active else ''}Pilih {style_name}", key=f"style_{style_name}", use_container_width=True):
            set_ss(visual_style=style_name)
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
btn_generate_titles = st.button("🚀 Generate Script & Judul", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)


# ─── SECTION 3: GENERATE JUDUL ───────────────────────────────────────────────
if btn_generate_titles:
    if not topic_input.strip():
        st.warning("⚠️ Masukkan topik video terlebih dahulu.")
    else:
        from core.youtube_service import riset_kompetitor, generate_7_titles

        with st.spinner("🔍 Riset kompetitor YouTube & generate 7 judul terbaik..."):
            try:
                # Buat job baru
                new_job_id = create_job(
                    topic=topic_input.strip(),
                    dna_profile_id=active_dna_id,
                    visual_style=current_style
                )
                set_ss(current_job_id=new_job_id, topic_input=topic_input.strip())

                # Riset kompetitor
                videos, tags = riset_kompetitor(topic_input, max_results=10)
                set_ss(competitor_tags=tags, competitor_videos=videos)

                # Generate 7 judul
                titles = generate_7_titles(topic_input, dna_text, videos, tags, prefer_groq=ss('prefer_groq', False))
                save_title_candidates(new_job_id, titles)

                st.success("✅ 7 judul berhasil digenerate!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# Tampilkan judul jika ada job aktif
if current_job_id:
    job_data = get_job(current_job_id)
    title_candidates = get_title_candidates(current_job_id)
    selected_title_row = get_selected_title(current_job_id)

    if title_candidates:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏆 Pilih Judul YouTube</div>', unsafe_allow_html=True)

        for tc in title_candidates:
            is_selected = tc['status'] == 'Terseleksi'
            status_badge = f'<span class="badge-selected">✓ Terseleksi</span>' if is_selected else f'<span class="badge-pending">Pending</span>'
            card_class = "title-card selected" if is_selected else "title-card"

            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"""
                <div class="{card_class}">
                  <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                    {status_badge}
                    <span style="font-weight:600; font-size:0.9rem; color:#E6EDF3;">{tc['title']}</span>
                  </div>
                  <div style="font-size:0.78rem; color:#7D8590;">💡 {tc.get('reason','')}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if not is_selected:
                    if st.button("Pilih", key=f"sel_title_{tc['id']}", use_container_width=True):
                        select_title(tc['id'], current_job_id)
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


    # ─── SECTION 4: GENERATE SCRIPT ──────────────────────────────────────────
    if selected_title_row:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✍️ Generate Script</div>', unsafe_allow_html=True)

        existing_script = get_script(current_job_id)
        script_content = existing_script['content'] if existing_script else ""
        char_count = len(script_content)

        c_btn, c_info = st.columns([1, 2])
        with c_btn:
            btn_gen_script = st.button(
                "🤖 Generate Script (10k–11k karakter)",
                type="primary",
                use_container_width=True,
                disabled=bool(existing_script and existing_script['status'] == 'saved')
            )
        with c_info:
            if existing_script:
                color = "#3FB950" if 10000 <= char_count <= 11000 else "#F0883E"
                st.markdown(f"""
                <div style="font-size:0.85rem; color:{color}; margin-top: 8px;">
                  📊 {char_count:,} karakter · {existing_script['status'].upper()}
                </div>
                """, unsafe_allow_html=True)

        if btn_gen_script:
            from core.script_generator import generate_full_script
            with st.spinner("✍️ Generating naskah YouTube (10k–11k karakter)... harap tunggu ~30 detik"):
                try:
                    script = generate_full_script(
                        title=selected_title_row['title'],
                        dna_text=dna_text,
                        visual_style=current_style,
                        prefer_groq=ss('prefer_groq', False)
                    )
                    save_script(current_job_id, selected_title_row['id'], script)
                    st.success(f"✅ Script berhasil digenerate! ({len(script):,} karakter)")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error generate script: {str(e)}")

        if script_content:
            st.markdown("---")
            st.markdown('<div class="section-title">📋 Editorial Script</div>', unsafe_allow_html=True)

            # Tombol audit vidIQ
            col_doc, col_aud = st.columns([3, 1])
            with col_aud:
                btn_audit = st.button("🔬 Audit vidIQ", use_container_width=True)

            edited_script = st.text_area(
                "Edit Script",
                value=script_content,
                height=300,
                label_visibility="collapsed",
                key="script_editor"
            )

            col_s1, col_s2 = st.columns([1, 1])
            with col_s1:
                if st.button("💾 Simpan Script", type="primary", use_container_width=True):
                    update_script_content(current_job_id, edited_script, 'saved')
                    st.success("✅ Script tersimpan!")
                    st.rerun()
            with col_s2:
                if st.button("🔄 Regenerate Script", use_container_width=True):
                    update_script_content(current_job_id, '', 'draft')
                    st.rerun()

            # vidIQ Audit Panel
            if btn_audit:
                from core.script_doctor import analisis_retensi_dan_seo
                competitor_tags = ss('competitor_tags', [])
                with st.spinner("🔍 Audit retensi & SEO..."):
                    hasil = analisis_retensi_dan_seo(edited_script, selected_title_row['title'], competitor_tags)
                    set_ss(audit_result=hasil)

            audit = ss('audit_result')
            if audit:
                st.markdown("---")
                st.markdown('<div class="section-title">📊 vidIQ Script Doctor</div>', unsafe_allow_html=True)

                mc1, mc2, mc3 = st.columns(3)
                score = audit['skor_seo']
                score_color = "#3FB950" if score >= 80 else "#F0883E" if score >= 60 else "#F85149"
                with mc1:
                    st.markdown(f"""<div class="metric-box">
                    <div class="metric-label">Skor SEO & Retensi</div>
                    <div class="metric-value" style="color:{score_color};">{score}<span style="font-size:1rem; color:#7D8590;">/100</span></div>
                    </div>""", unsafe_allow_html=True)
                with mc2:
                    trim_count = len(audit['kalimat_perlu_dihapus'])
                    st.markdown(f"""<div class="metric-box">
                    <div class="metric-label">Perlu Di-Trim</div>
                    <div class="metric-value" style="color:#F85149;">{trim_count}</div>
                    </div>""", unsafe_allow_html=True)
                with mc3:
                    st.markdown(f"""<div class="metric-box" style="text-align:left;">
                    <div class="metric-label">💡 Saran Taktis</div>
                    <div style="font-size:0.8rem; color:#E6EDF3; line-height:1.4; margin-top:4px;">{audit['saran_optimasi']}</div>
                    </div>""", unsafe_allow_html=True)

                tab_trim, tab_kw = st.tabs(["✂️ Trim Audit", "🎯 Kata Kunci"])
                with tab_trim:
                    items = audit.get('kalimat_perlu_dihapus', [])
                    if items:
                        for idx, item in enumerate(items, 1):
                            st.markdown(f"""<div class="trim-card">
                            <div class="trim-text">#{idx} "{item['kalimat'][:150]}"</div>
                            <div class="trim-reason"><b>Alasan:</b> {item['alasan']}</div>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.success("🎉 Naskah bebas dari filler phrases!")
                with tab_kw:
                    kc1, kc2 = st.columns(2)
                    with kc1:
                        st.markdown("**✅ Kata Kunci Ditemukan**")
                        found = audit.get('kata_kunci_ditemukan', [])
                        if found:
                            st.markdown("".join([f'<span class="badge-green">✓ {kw}</span>' for kw in found]), unsafe_allow_html=True)
                        else:
                            st.info("Belum ada kata kunci utama terdeteksi.")
                    with kc2:
                        st.markdown("**⚡ Rekomendasi Kata Kunci**")
                        rec = audit.get('rekomendasi_kata_kunci', [])
                        if rec:
                            st.markdown("".join([f'<span class="badge-blue">+ {kw}</span>' for kw in rec]), unsafe_allow_html=True)
                        else:
                            st.success("Kata kunci sudah optimal!")

        st.markdown("</div>", unsafe_allow_html=True)


    # ─── SECTION 5: GENERATE 45 SCENES ───────────────────────────────────────
    current_script = get_script(current_job_id)
    if current_script and current_script.get('status') == 'saved' and current_script.get('content'):
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎬 Generate 45 Scenes</div>', unsafe_allow_html=True)

        scenes = get_scenes(current_job_id)
        summary = get_scenes_summary(current_job_id) if scenes else {"total": 0, "audio_done": 0, "image_done": 0}

        c_gbtn, c_progress = st.columns([1, 2])
        with c_gbtn:
            btn_gen_scenes = st.button(
                "⚡ Generate All Scenes",
                type="primary",
                use_container_width=True,
                disabled=len(scenes) == 45
            )
        with c_progress:
            if scenes:
                st.markdown(f"""<div style="margin-top:8px; font-size:0.85rem; color:#7D8590;">
                  🎬 {summary['total']} scenes · 🖼️ {summary['image_done']} gambar · 🎙️ {summary['audio_done']} audio
                </div>""", unsafe_allow_html=True)
                prog_val = (summary['image_done'] + summary['audio_done']) / (summary['total'] * 2) if summary['total'] > 0 else 0
                st.progress(min(prog_val, 1.0))

        if btn_gen_scenes:
            from core.scene_splitter import split_script_to_scenes
            job_info = get_job(current_job_id)
            with st.spinner("✂️ Memecah naskah menjadi 45 scene... harap tunggu ~30 detik"):
                try:
                    scene_list = split_script_to_scenes(
                        script=current_script['content'],
                        title=selected_title_row['title'] if selected_title_row else "Video YouTube",
                        dna_text=dna_text,
                        visual_style=current_style,
                        character_description="",
                        prefer_groq=ss('prefer_groq', False)
                    )
                    save_scenes(current_job_id, scene_list)
                    st.success(f"✅ {len(scene_list)} scene berhasil dibuat!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)


    # ─── SECTION 6: SCENE CARDS ───────────────────────────────────────────────
    scenes = get_scenes(current_job_id)
    if scenes:
        from core.voiceover_service import VOICE_OPTIONS, DEFAULT_VOICE, generate_voiceover, audio_exists, get_audio_path
        from core.image_service import generate_scene_image, image_exists, get_image_path

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎞️ Scene Manager</div>', unsafe_allow_html=True)

        # Pengaturan voiceover
        v_col1, v_col2, v_col3 = st.columns([2, 1, 1])
        with v_col1:
            selected_voice_label = st.selectbox("🎙️ Suara Voiceover", list(VOICE_OPTIONS.keys()), index=0)
            selected_voice = VOICE_OPTIONS[selected_voice_label]
        with v_col2:
            voice_rate = st.selectbox("Kecepatan", ["-10%", "+0%", "+10%", "+20%"], index=1)
        with v_col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎙️ Generate ALL Voiceover", use_container_width=True):
                prog = st.progress(0)
                status_txt = st.empty()
                for i, scene in enumerate(scenes):
                    scene_num = scene['scene_number']
                    status_txt.markdown(f"Generating voiceover scene {scene_num}/45...")
                    try:
                        audio_path = generate_voiceover(scene['narasi'], current_job_id, scene_num, selected_voice, voice_rate)
                        update_scene(scene['id'], audio_path=audio_path, audio_status='done')
                    except Exception as e:
                        update_scene(scene['id'], audio_status=f'error')
                    prog.progress((i + 1) / len(scenes))
                status_txt.markdown("✅ Semua voiceover selesai!")
                st.rerun()

        st.markdown("---")

        # Scene cards (tampilkan 5 per baris)
        for i in range(0, len(scenes), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j >= len(scenes):
                    break
                scene = scenes[i + j]
                scene_num = scene['scene_number']
                scene_id = scene['id']

                audio_done = scene.get('audio_status') == 'done'
                image_done = scene.get('image_status') == 'done'
                all_done = audio_done and image_done

                with col:
                    status_cls = "done" if all_done else ""
                    status_badge = f'<span class="scene-status-done">done</span>' if all_done else f'<span class="scene-status-pending">pending</span>'
                    st.markdown(f"""
                    <div class="scene-card {status_cls}">
                      <div class="scene-header">
                        <span class="scene-num">Scene {scene_num}</span>
                        {status_badge}
                      </div>
                      <div class="field-label">Narasi</div>
                      <div class="narasi-box">{scene.get('narasi','')[:250]}</div>
                      <div class="field-label">Visual Prompt</div>
                      <div class="prompt-box">{scene.get('visual_prompt','')[:200]}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Tombol generate
                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        # Voiceover
                        if audio_done:
                            apath = scene.get('audio_path') or get_audio_path(current_job_id, scene_num)
                            if os.path.exists(apath):
                                st.audio(apath, format='audio/mp3')
                        else:
                            if st.button(f"🎙️ Voiceover", key=f"vo_{scene_id}", use_container_width=True):
                                with st.spinner(f"Generating audio scene {scene_num}..."):
                                    try:
                                        apath = generate_voiceover(scene['narasi'], current_job_id, scene_num, selected_voice, voice_rate)
                                        update_scene(scene_id, audio_path=apath, audio_status='done')
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")

                    with btn_cols[1]:
                        # Generate Image
                        if image_done:
                            ipath = scene.get('image_path') or get_image_path(current_job_id, scene_num)
                            if os.path.exists(ipath):
                                st.image(ipath, use_container_width=True)
                        else:
                            if st.button(f"🖼️ Gambar", key=f"img_{scene_id}", use_container_width=True):
                                with st.spinner(f"Generating image scene {scene_num}..."):
                                    try:
                                        ipath = generate_scene_image(
                                            scene.get('visual_prompt', ''),
                                            current_job_id,
                                            scene_num,
                                            char_image_path
                                        )
                                        update_scene(scene_id, image_path=ipath, image_status='done')
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)


    # ─── SECTION 7: DOWNLOAD ALL ─────────────────────────────────────────────
    if scenes:
        from core.exporter import create_export_zip, get_export_stats

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📦 Download All Assets</div>', unsafe_allow_html=True)

        stats = get_export_stats(current_job_id, scenes)
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f"""<div class="metric-box">
            <div class="metric-label">Total Scenes</div>
            <div class="metric-value" style="color:#79C0FF;">{stats['total_scenes']}</div>
            </div>""", unsafe_allow_html=True)
        with s2:
            st.markdown(f"""<div class="metric-box">
            <div class="metric-label">Gambar Ready</div>
            <div class="metric-value" style="color:#3FB950;">{stats['images_ready']}</div>
            </div>""", unsafe_allow_html=True)
        with s3:
            st.markdown(f"""<div class="metric-box">
            <div class="metric-label">Audio Ready</div>
            <div class="metric-value" style="color:#3FB950;">{stats['audio_ready']}</div>
            </div>""", unsafe_allow_html=True)
        with s4:
            st.markdown(f"""<div class="metric-box">
            <div class="metric-label">Video Ready</div>
            <div class="metric-value" style="color:#3FB950;">{stats['videos_ready']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        job_title = selected_title_row['title'] if selected_title_row else f"job_{current_job_id}"

        if any([stats['images_ready'] > 0, stats['audio_ready'] > 0]):
            zip_bytes = create_export_zip(current_job_id, job_title, scenes)
            safe_title = job_title[:40].replace(' ', '_')
            st.download_button(
                label="⬇️ Download ZIP Semua Aset",
                data=zip_bytes,
                file_name=f"orchestra_{safe_title}.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary"
            )
        else:
            st.info("⚠️ Belum ada aset yang siap di-download. Generate gambar & voiceover terlebih dahulu.")

        st.markdown("</div>", unsafe_allow_html=True)
