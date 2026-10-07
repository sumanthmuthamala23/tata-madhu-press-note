import os
import io
import time
import json
import base64
import tempfile
import datetime
import urllib.parse
import requests
import streamlit as st
from PIL import Image
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from google import genai
from google.genai import types

# Page setup
st.set_page_config(
    page_title="MLC తాతా మధు - అధికారిక పత్రికా ప్రకటన కన్సోల్",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="auto"
)

# Helper to read and encode local files to base64
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# Crop top header from letterhead.png (Top ~18-19%)
def get_cropped_letterhead_banner(image_path):
    if os.path.exists(image_path):
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                header_box = (0, 0, width, int(height * 0.19))
                cropped = img.crop(header_box)
                buffer = io.BytesIO()
                cropped.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode()
        except Exception:
            return get_base64_image(image_path)
    return None

bg_image_base64 = get_base64_image("background.png")
dev_image_base64 = get_base64_image("Sumanth.jpg") or get_base64_image("sumanth.jpg")

# Locate letterhead file
lh_filename = None
for fname in ["letterhead.png", "letter head(2).jpg", "letterhead.jpg"]:
    if os.path.exists(fname):
        lh_filename = fname
        break

lh_banner_base64 = get_cropped_letterhead_banner(lh_filename) if lh_filename else None

if bg_image_base64:
    bg_style = f"""
    .stApp {{
        background: linear-gradient(135deg, rgba(255, 245, 248, 0.96) 0%, rgba(255, 255, 255, 0.98) 100%),
                    url("data:image/png;base64,{bg_image_base64}");
        background-size: cover;
        background-position: center top;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    """
else:
    bg_style = """
    .stApp {
        background: linear-gradient(135deg, #fff1f5 0%, #ffffff 50%, #fff5f8 100%);
        background-attachment: fixed;
    }
    """

# Custom CSS with Anek Telugu Font
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Anek+Telugu:wght@300;400;500;600;700;800&display=swap');
    
    {bg_style}
    
    html, body, p, div:not([data-testid="stIconMaterial"]), h1, h2, h3, h4, h5, h6, input, textarea, button {{
        font-family: 'Anek Telugu', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    span[data-testid="stIconMaterial"], .material-symbols-rounded, .material-symbols-outlined {{
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
        font-size: 22px !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #fff2f6 !important;
        border-right: 1.5px solid #fecdd3;
        box-shadow: 2px 0 14px rgba(225, 29, 72, 0.05);
    }}

    .header-card {{
        background: linear-gradient(90deg, #991b1b 0%, #be123c 65%, #e11d48 100%);
        color: #ffffff !important;
        padding: 22px 30px;
        border-radius: 14px;
        box-shadow: 0 8px 24px rgba(184, 35, 41, 0.22);
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    .header-card h1 {{
        color: #ffffff !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        line-height: 1.3 !important;
    }}
    .header-card p {{
        color: #ffe4e6 !important;
        font-size: 14px !important;
        margin: 6px 0 0 0 !important;
        font-weight: 500 !important;
    }}

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-size: 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }}
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
        border-color: #be123c !important;
        box-shadow: 0 0 0 2px rgba(190, 18, 60, 0.15) !important;
    }}

    div.stButton > button[kind="primary"] {{
        background: linear-gradient(90deg, #991b1b 0%, #be123c 100%) !important;
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 14px rgba(190, 18, 60, 0.3) !important;
        transition: all 0.2s ease !important;
    }}
    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(190, 18, 60, 0.45) !important;
    }}

    .letterhead-container {{
        background-color: #ffffff;
        border: 1.5px solid #cbd5e1;
        border-radius: 8px;
        padding: 35px 48px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        color: #111111;
        line-height: 1.95;
        font-size: 18px;
        max-width: 860px;
        margin: 0 auto;
        box-sizing: border-box;
    }}

    .letterhead-banner-img {{
        width: 100%;
        max-height: 180px;
        object-fit: contain;
        display: block;
        margin: 0 auto 16px auto;
        border-bottom: 2px solid #b82329;
        padding-bottom: 8px;
    }}

    .dev-badge {{
        display: flex;
        align-items: center;
        gap: 12px;
        background: #ffffff;
        border: 1.5px solid #fecdd3;
        border-radius: 14px;
        padding: 10px 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-top: 15px;
    }}
    .dev-img {{
        width: 52px;
        height: 52px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #be123c;
        flex-shrink: 0;
    }}
    .dev-text {{
        font-size: 13px;
        font-weight: 700;
        color: #1e293b;
        line-height: 1.25;
    }}
    .dev-sub {{
        font-size: 11px;
        color: #be123c;
        font-weight: 600;
        margin-top: 3px;
        line-height: 1.3;
    }}

    .sidebar-emblem-card {{
        display: flex;
        align-items: center;
        gap: 12px;
        background: #ffffff;
        padding: 10px 14px;
        border-radius: 12px;
        border: 1.5px solid #fecdd3;
        margin-bottom: 15px;
    }}
    .sidebar-emblem-icon {{
        font-size: 30px;
        background: #fff1f5;
        border-radius: 8px;
        padding: 4px 8px;
    }}
    .sidebar-emblem-title {{
        font-weight: 800;
        color: #be123c;
        font-size: 17px;
        line-height: 1.2;
    }}
    .sidebar-emblem-subtitle {{
        font-size: 12px;
        color: #64748b;
        font-weight: 600;
    }}

    @media screen and (max-width: 768px) {{
        .header-card {{
            padding: 16px 18px !important;
        }}
        .header-card h1 {{
            font-size: 20px !important;
        }}
        .letterhead-container {{
            padding: 18px 16px !important;
            font-size: 16px !important;
            line-height: 1.75 !important;
        }}
        .letterhead-banner-img {{
            max-height: 110px !important;
            margin-bottom: 10px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# ----------------- SYSTEM INSTRUCTION -----------------
SYSTEM_INSTRUCTION = (
    "You are the EXCLUSIVE Chief Media Secretary & Official Telugu Press Spokesperson "
    "for Sri Tata Madhusudhan (Tata Madhu) Garu, Member of Legislative Council (MLC), "
    "Bharat Rashtra Samithi (BRS).\n\n"
    "STRICT CONSTRAINTS:\n"
    "1. LEADER EXCLUSIVITY: Every statement, critique, demand, condolence, or declaration must be strictly attributed "
    "to MLC Tata Madhusudhan (శాసనమండలి సభ్యులు తాతా మధుసూదన్ / తాతా మధు). Under no circumstances generate releases for anyone else.\n"
    "2. VIDEO / AUDIO / NOTES HANDLING: When notes, condolences, audio, or video are provided, capture the exact core message, "
    "facts, sentiments, condolences, or political demands immediately and accurately.\n"
    "3. NO JURISDICTION BOUNDARIES: He speaks on statewide governance, legislative council debates, Hyderabad affairs, national topics, and grassroots public grievances.\n"
    "4. JOURNALISTIC TELUGU: Write in standard high-register journalistic Telugu (ప్రామాణిక పత్రికా భాష) formatted for Telugu daily newspapers (Eenadu, Sakshi, Namasthe Telangana, Andhra Jyothy, etc.).\n"
    "5. STRUCTURE:\n"
    "   - Header: అధికారిక పత్రికా ప్రకటన\n"
    "   - స్థలం & తేదీ\n"
    "   - ప్రధాన శీర్షిక (Impactful headline highlighting 'ఎమ్మెల్సీ తాతా మధు')\n"
    "   - లీడ్ పేరా (Who, What, Where, When, and primary declaration/condolence)\n"
    "   - ముఖ్యాంశాలు (3 to 5 clear bulleted points)\n"
    "   - ముగింపు (Closing remarks and official endorsement)\n"
    "   - విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం\n"
)

# Transliteration Helper
def google_transliterate_telugu(text: str) -> str:
    if not text.strip():
        return ""
    words = text.split()
    converted_words = []
    url = "https://inputtools.google.com/request?text={}&itc=te-t-i0-und&num=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    for word in words:
        if word.isdigit() or word in [",", ".", "!", "?", "-", ":", ";"]:
            converted_words.append(word)
            continue
        try:
            req_url = url.format(urllib.parse.quote(word))
            res = requests.get(req_url, headers=headers, timeout=5)
            data = res.json()
            if data[0] == "SUCCESS" and len(data[1][0][1]) > 0:
                converted_words.append(data[1][0][1][0])
            else:
                converted_words.append(word)
        except Exception:
            converted_words.append(word)
    return " ".join(converted_words)

# Ultra-Fast Zero-Lag Generation Engine (Verified active endpoints only)
def generate_ai_response(keys: list, contents_list: list, system_instruction=SYSTEM_INSTRUCTION, temperature=0.3):
    last_error = None
    # Verified active low-latency models for google-genai SDK
    models_to_try = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
    
    for key in keys:
        if not key or not key.strip():
            continue
        try:
            client = genai.Client(api_key=key.strip())
            for model_name in models_to_try:
                try:
                    res = client.models.generate_content(
                        model=model_name,
                        contents=contents_list,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=temperature,
                        ),
                    )
                    if res and res.text:
                        return res.text
                except Exception as model_err:
                    last_error = model_err
                    continue
        except Exception as client_err:
            last_error = client_err
            continue
            
    if last_error:
        raise last_error
    raise RuntimeError("API key unavailable or quota exceeded.")

# DOCX Generator
def create_docx_press_note(text: str, date_str: str, location_str: str) -> io.BytesIO:
    doc = Document()
    p_header = doc.add_paragraph()
    run_name = p_header.add_run("TATA MADHUSUDHAN\n")
    run_name.font.name = "Arial"
    run_name.font.size = Pt(16)
    run_name.bold = True
    run_name.font.color.rgb = RGBColor(184, 35, 41)
    
    run_desig = p_header.add_run("M.L.C\nKhammam, Telangana\n")
    run_desig.font.name = "Arial"
    run_desig.font.size = Pt(11)
    run_desig.bold = True
    
    run_hq = p_header.add_run(
        "Quarter No. 1104, 11th Floor, M.S. Block-III, Old MLA Quarters, "
        "Hyderguda, Hyderabad - 500029 | e-mail: tatamadhu@gmail.com\n"
    )
    run_hq.font.name = "Arial"
    run_hq.font.size = Pt(9)
    run_hq.font.color.rgb = RGBColor(100, 100, 100)
    
    doc.add_paragraph("―" * 55)
    
    p_meta = doc.add_paragraph(f"స్థలం: {location_str} | తేదీ: {date_str}\n")
    p_meta.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    for line in text.split("\n"):
        if line.strip():
            p = doc.add_paragraph(line.strip())
            p.paragraph_format.line_spacing = 1.3
            p.paragraph_format.space_after = Pt(6)
            
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# Printable HTML Template with Top Banner Crop
def get_printable_letterhead_html(content: str, date_str: str, location_str: str, lh_base64: str) -> str:
    if lh_base64:
        header_html = f"""
        <div style="width: 100%; max-height: 180px; overflow: hidden; border-bottom: 2px solid #b82329; margin-bottom: 20px;">
            <img src="data:image/png;base64,{lh_base64}" style="width: 100%; object-fit: cover; object-position: top center;" />
        </div>
        """
    else:
        header_html = """
        <div style="border-bottom: 2px solid #b82329; padding-bottom: 12px; margin-bottom: 20px;">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 40%; vertical-align: top;">
                        <h2 style="color: #b82329; margin: 0; font-size: 22px; font-weight: 800;">TATA MADHUSUDHAN</h2>
                        <div style="font-size: 15px; font-weight: bold;">M.L.C</div>
                        <div style="font-size: 13px; color: #555;">Khammam, Telangana</div>
                    </td>
                    <td style="width: 20%; text-align: center; vertical-align: middle;">
                        <div style="font-size: 40px;">🏛️</div>
                    </td>
                    <td style="width: 40%; text-align: right; vertical-align: top; font-size: 11px; color: #444; line-height: 1.4;">
                        Quarter No. 1104, 11th Floor,<br>
                        M.S. Block-III, Old MLA Quarters,<br>
                        Hyderguda, Hyderabad - 500029<br>
                        e-mail: tatamadhu@gmail.com
                    </td>
                </tr>
            </table>
        </div>
        """

    clean_content = content.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MLC Tata Madhusudhan Press Note</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Anek+Telugu:wght@400;600;700;800&display=swap');
    body {{
        font-family: 'Anek Telugu', sans-serif;
        background-color: #ffffff;
        margin: 0;
        padding: 20px;
        color: #111;
    }}
    .container {{
        max-width: 800px;
        margin: 0 auto;
        padding: 10px 20px;
        box-sizing: border-box;
    }}
    .meta {{
        text-align: right;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 18px;
        color: #374151;
    }}
    .content {{
        font-size: 17px;
        line-height: 1.95;
    }}
    @media print {{
        body {{ padding: 0; }}
        .container {{ border: none; padding: 0; }}
        .no-print {{ display: none; }}
    }}
</style>
</head>
<body>
<div class="no-print" style="text-align: center; margin-bottom: 25px;">
    <button onclick="window.print()" style="padding: 12px 28px; font-size: 16px; font-weight: bold; background-color: #b82329; color: white; border: none; border-radius: 6px; cursor: pointer;">
        🖨️ నేరుగా ప్రింట్ / PDF తీయండి (Print or Save as PDF)
    </button>
</div>
<div class="container">
    {header_html}
    <div class="meta">స్థలం: {location_str} &nbsp;|&nbsp; తేదీ: {date_str}</div>
    <div class="content">
        {clean_content}
    </div>
    <div style="border-top: 1px dashed #b82329; margin-top: 35px; padding-top: 12px; text-align: right; font-weight: bold; color: #444;">
        విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
    </div>
</div>
</body>
</html>"""

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-emblem-card">
        <div class="sidebar-emblem-icon">🚗</div>
        <div>
            <div class="sidebar-emblem-title">BRS Party</div>
            <div class="sidebar-emblem-subtitle">భారత రాష్ట్ర సమితి</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### సెట్టింగ్స్ (Settings)")
    
    default_key = ""
    backup_key = ""
    try:
        if hasattr(st, "secrets"):
            default_key = st.secrets.get("GEMINI_API_KEY", "")
            backup_key = st.secrets.get("BACKUP_API_KEY", "")
    except Exception:
        pass

    api_key_input = st.text_input(
        "Gemini API Key",
        value=default_key,
        type="password",
        help="Google AI Studio API Key ఇక్కడ నమోదు చేయండి."
    )
    
    st.markdown("##### 📅 ప్రకటన తేదీ (Date):")
    selected_date = st.date_input("తేదీని ఎంచుకోండి", value=datetime.date.today())
    formatted_date = selected_date.strftime("%d-%m-%Y")
    
    st.markdown("##### 📍 స్థలం / వేదిక (Location):")
    if "final_loc_key" not in st.session_state:
        st.session_state["final_loc_key"] = "ఖమ్మం"
        
    loc_eng = st.text_input("ఇంగ్లీష్‌లో టైప్ చేయండి:", placeholder="e.g. Khammam, Palair, Hyderabad...", key="loc_eng_input")
    if st.button("🔄 స్థలాన్ని తెలుగులోకి మార్చండి", use_container_width=True):
        if loc_eng.strip():
            converted_loc = google_transliterate_telugu(loc_eng)
            st.session_state["final_loc_key"] = converted_loc
            st.rerun()

    final_location = st.text_input(
        "ఫైనల్ స్థలం (Telugu Location):", 
        key="final_loc_key"
    )

    topic_scopes = [
        "శుభాకాంక్షలు & సంతాపాలు (Greetings & Condolences)",
        "ప్రజా సమస్యలు & వినతులు (Public Grievances & Demands)",
        "ప్రభుత్వ విధానాలు / విమర్శలు (State Govt Policies / Criticisms)",
        "రైతాంగ & వ్యవసాయ సమస్యలు (Farmers & Agriculture Issues)",
        "శాసనమండలి ప్రసంగాలు / ప్రశ్నలు (Council Speeches & Legislative Issues)",
        "నియోజకవర్గ అభివృద్ధి & నిధులు (Constituency Development & Sanctions)",
        "పార్టీ కార్యక్రమాలు & సమావేశాలు (Party Meetings & Organizational)",
        "నిరసనలు, ధర్నాలు & పోరాటాలు (Protests & Agitations)",
        "అధికారులతో సమీక్షలు / వినతులు (Official Reviews & Representations)",
        "సేవా కార్యక్రమాలు & సంక్షేమం (Social Welfare & Charity)",
    ]
    selected_scope = st.selectbox("ప్రకటన విభాగం / స్వభావం (Topic Scope)", topic_scopes)

    # Developer Attribution Badge in Sidebar
    st.markdown("---")
    dev_img_html = f'<img src="data:image/jpeg;base64,{dev_image_base64}" class="dev-img">' if dev_image_base64 else '<span style="font-size:26px;">👨‍💻</span>'
    st.markdown(f"""
    <div class="dev-badge">
        {dev_img_html}
        <div>
            <div class="dev-text">Designed & Developed by<br>Sumanth Muthamala</div>
            <div class="dev-sub">Revenue Inspector & PA to MLC Khammam</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

active_keys = [api_key_input]
if backup_key and backup_key != api_key_input:
    active_keys.append(backup_key)

# ----------------- MAIN UI -----------------
st.markdown(f"""
<div class="header-card">
    <h1>🎙️ ఎమ్మెల్సీ తాతా మధుసూదన్ — అధికారిక పత్రికా ప్రకటన కన్సోల్</h1>
    <p>తేదీ: {formatted_date} &nbsp;|&nbsp; స్థలం: {final_location} &nbsp;|&nbsp; శాసనమండలి మీడియా సమన్వయ విభాగం</p>
</div>
""", unsafe_allow_html=True)

if not api_key_input:
    st.warning("ముందుగా సైడ్‌బార్‌లో మీ Gemini API Keyని నమోదు చేయండి.")
    st.stop()

if "audio_file_payload" not in st.session_state:
    st.session_state["audio_file_payload"] = None

input_parts = []

input_mode = st.radio(
    "ఇన్‌పుట్ విధానం ఎంచుకోండి (Input Mode):",
    ["✍️ సిట్యుయేషన్ నోట్స్ (Text)", "📁 ఆడియో / వీడియో ఫైల్ అప్‌లోడ్ (File)", "🎤 లైవ్ రికార్డింగ్ (Mic)"],
    index=0,
    horizontal=True
)

st.write("")

if input_mode == "✍️ సిట్యుయేషన్ నోట్స్ (Text)":
    st.markdown("##### ఇంగ్లీష్ ➔ తెలుగు మార్పిడి (English Typing to Telugu):")
    with st.expander("🔤 ఇంగ్లీష్/టాంగ్లీష్‌లో టైప్ చేసి తెలుగులోకి మార్చండి", expanded=False):
        raw_eng = st.text_area(
            "ఇంగ్లీష్ లేదా టాంగ్లీష్ (Tanglish) లో టైప్ చేయండి:",
            placeholder="ఉదాహరణ: Rythu Bandu inka Raledu, Tata Madhu garu mandapaddaru...",
            height=85,
            key="raw_eng_text"
        )
        if st.button("🔄 తెలుగులోకి మార్చండి (Convert to Telugu)", use_container_width=True):
            if raw_eng.strip():
                with st.spinner("తెలుగులోకి మారుస్తోంది..."):
                    converted = google_transliterate_telugu(raw_eng)
                    st.session_state["final_notes_area"] = converted
                    st.rerun()
            else:
                st.warning("దయచేసి ఇంగ్లీష్‌లో టెక్స్ట్ టైప్ చేయండి.")

    st.markdown("##### పత్రికా ప్రకటన కోసం ముఖ్యాంశాలు (Notes):")
    notes_text = st.text_area(
        "తెలుగు వివరాలు (నేరుగా ఇక్కడ నమోదు చేయండి లేదా సవరించుకోండి):",
        height=140,
        value=st.session_state.get("final_notes_area", ""),
        key="notes_text_area",
        placeholder="ఇక్కడ వివరాలు రాయండి (ఉదా: సంతాప ప్రకటన, సభ వివరాలు, రైతు సమస్యలు...)"
    )
    if notes_text.strip():
        input_parts.append(types.Part.from_text(text=notes_text))

elif input_mode == "📁 ఆడియో / వీడియో ఫైల్ అప్‌లోడ్ (File)":
    st.markdown("##### 📁 మొబైల్ లేదా ల్యాప్‌టాప్ రికార్డింగ్ ఫైల్ ఎంచుకోండి:")
    
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        uploaded_file = st.file_uploader(
            "ఆడియో లేదా వీడియో ఫైల్ ఎంచుకోండి (.m4a, .mp3, .wav, .mp4, etc.):",
            type=None,
            key="pinned_mobile_audio_uploader"
        )
    with col_f2:
        if st.session_state.get("audio_file_payload"):
            if st.button("🗑️ ఫైల్ తొలగించు (Clear File)", use_container_width=True):
                st.session_state["audio_file_payload"] = None
                st.rerun()

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        f_name = uploaded_file.name
        fn_low = f_name.lower()

        if fn_low.endswith((".m4a", ".aac")) or "m4a" in (uploaded_file.type or "").lower():
            clean_mime = "audio/mp4"
        elif fn_low.endswith(".mp3"):
            clean_mime = "audio/mp3"
        elif fn_low.endswith(".wav"):
            clean_mime = "audio/wav"
        elif fn_low.endswith((".ogg", ".opus")):
            clean_mime = "audio/ogg"
        elif fn_low.endswith((".mp4", ".m4v")):
            clean_mime = "video/mp4"
        elif fn_low.endswith(".mov"):
            clean_mime = "video/quicktime"
        else:
            clean_mime = "audio/mp4"

        st.session_state["audio_file_payload"] = (f_name, file_bytes, clean_mime)

    if st.session_state.get("audio_file_payload"):
        fn, fb, fm = st.session_state["audio_file_payload"]
        st.success(f"✅ ఫైల్ సిద్ధంగా ఉంది: **{fn}** ({len(fb)/(1024*1024):.2f} MB)")

elif input_mode == "🎤 లైవ్ రికార్డింగ్ (Mic)":
    st.markdown("##### మైక్ ద్వారా మాట్లాడి రికార్డ్ చేయండి:")
    live_audio = st.audio_input("వాయిస్ రికార్డ్ చేయండి")
    if live_audio:
        st.success("✅ ఆడియో రికార్డ్ అయ్యింది!")
        audio_bytes = live_audio.read()
        input_parts.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"))

st.divider()

if st.button("🚀 పత్రికా ప్రకటనను రూపొందించండి (Generate Press Note)", type="primary", use_container_width=True):
    # Assemble media payload right before generating
    if input_mode == "📁 ఆడియో / వీడియో ఫైల్ అప్‌లోడ్ (File)" and st.session_state.get("audio_file_payload"):
        fn, fb, fm = st.session_state["audio_file_payload"]
        if len(fb) > 20 * 1024 * 1024:
            file_ext = os.path.splitext(fn)[1] or (".mp4" if "video" in fm else ".m4a")
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                tmp.write(fb)
                tmp_path = tmp.name
            with st.spinner(f"పెద్ద మీడియా ఫైల్ ({fn}) ప్రాసెస్ అవుతోంది... దయచేసి వేచి ఉండండి..."):
                try:
                    c = genai.Client(api_key=active_keys[0])
                    up_ref = c.files.upload(file=tmp_path)
                    
                    if "video" in fm:
                        while up_ref.state.name == "PROCESSING":
                            time.sleep(2)
                            up_ref = c.files.get(name=up_ref.name)
                            
                    input_parts.append(up_ref)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
        else:
            input_parts.append(types.Part.from_bytes(data=fb, mime_type=fm))

    if not input_parts:
        st.error("⚠️ దయచేసి వివరాలు నమోదు చేయండి (నోట్స్, ఆడియో లేదా వీడియో).")
    else:
        with st.spinner("⚡ పత్రికా ప్రకటన తక్షణమే సిద్ధమవుతోంది..."):
            try:
                prompt_instruction = (
                    f"\nప్రకటన విభాగం / స్వభావం: {selected_scope}\n"
                    f"స్థలం: {final_location}\n"
                    f"తేదీ: {formatted_date}\n"
                    "దయచేసి అందించిన సమాచారం ఆధారంగా "
                    "ఎమ్మెల్సీ తాతా మధుసూదన్ గారి అధికారిక పత్రికా ప్రకటనను రూపొందించండి.\n"
                )
                parts_with_prompt = input_parts + [prompt_instruction]
                press_note_telugu = generate_ai_response(active_keys, parts_with_prompt)
                st.session_state["draft_note"] = press_note_telugu
                st.session_state["final_note"] = press_note_telugu
                st.session_state["is_finalized"] = False
            except Exception as e:
                st.error(f"సర్వర్ లోపం: {str(e)}")

# Display, Edit & AI Suggestion Refinement Section
if "draft_note" in st.session_state:
    st.subheader("✏️ ఎడిట్ & AI సలహాలు (Edit & AI Remarks)")
    
    edited_note = st.text_area(
        "ముసాయిదాను ఇక్కడ పరిశీలించి నేరుగా సవరించవచ్చు:",
        value=st.session_state.get("draft_note", ""),
        height=260,
        key="editor_area"
    )
    
    st.markdown("##### 🤖 జెమినీ AI సలహా / మోడ్ మార్పు (AI Tone & Situation Re-generator):")
    with st.expander("💡 ప్రెస్ నోట్ మార్పులు (రైతుల ఆవేదన పెంచడం, వివరాలు చేర్చడం, స్పష్టత ఇవ్వడం)", expanded=False):
        ai_remark = st.text_input(
            "మీ సూచన లేదా అభ్యర్థనను ఇక్కడ రాయండి (English or Telugu):",
            placeholder="e.g., 'రైతుల ఆవేదనను మరింత భావోద్వేగంగా మార్చండి', 'Add demand for immediate relief'..."
        )
        if st.button("⚡ సూచన ఆధారంగా ప్రెస్ నోట్ తిరిగి రూపొందించండి (Re-generate with AI)", use_container_width=True):
            if ai_remark.strip():
                with st.spinner("మీ సూచన ప్రకారం ప్రెస్ నోట్‌ను సరిచేస్తోంది..."):
                    try:
                        refine_prompt = f"""
                        CURRENT PRESS NOTE DRAFT:
                        {edited_note}
                        
                        USER INSTRUCTION / REMARK / SITUATION UPDATE:
                        {ai_remark}
                        
                        TASK:
                        Rewrite and refine the press release strictly following the user's instructions while maintaining the official persona of MLC Tata Madhusudhan Garu and standard Telugu journalistic standards.
                        """
                        updated_note = generate_ai_response(active_keys, [refine_prompt])
                        st.session_state["draft_note"] = updated_note
                        st.session_state["final_note"] = updated_note
                        st.success("✅ మీ సూచన ప్రకారం ప్రెస్ నోట్ విజయవంతంగా మార్చబడింది!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"రీ-జనరేట్ ఎర్రర్: {str(err)}")
            else:
                st.warning("దయచేసి మార్పుల కోసం సూచనను నమోదు చేయండి.")

    st.write("")
    if st.button("✅ పూర్తయింది - లెటర్‌హెడ్ & సోషల్ మీడియా వీక్షించండి (Finalize)", type="primary", use_container_width=True):
        st.session_state["final_note"] = edited_note
        st.session_state["is_finalized"] = True
        st.success("ప్రెస్ నోట్ ఖరారైంది! అధికారిక లెటర్‌హెడ్ వీక్షణ సిద్ధంగా ఉంది.")

# Official Canvas & Multi-Platform Social Media Hub
if st.session_state.get("is_finalized", False):
    final_content = st.session_state.get("final_note", "")
    
    st.divider()
    st.subheader("📄 అధికారిక లెటర్‌హెడ్ వీక్షణ (Official Letterhead View)")
    
    if lh_banner_base64:
        banner_img_html = f'<img src="data:image/png;base64,{lh_banner_base64}" class="letterhead-banner-img" alt="Official Letterhead">'
    else:
        banner_img_html = """
        <div style="border-bottom: 2px solid #b82329; padding-bottom: 12px; margin-bottom: 20px;">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 40%; vertical-align: top;">
                        <h2 style="color: #b82329; margin: 0; font-size: 22px; font-weight: 800;">TATA MADHUSUDHAN</h2>
                        <div style="font-size: 15px; font-weight: bold;">M.L.C</div>
                        <div style="font-size: 13px; color: #555;">Khammam, Telangana</div>
                    </td>
                    <td style="width: 20%; text-align: center; vertical-align: middle;">
                        <div style="font-size: 38px;">🏛️</div>
                    </td>
                    <td style="width: 40%; text-align: right; vertical-align: top; font-size: 11px; color: #444; line-height: 1.4;">
                        Quarter No. 1104, 11th Floor,<br>
                        M.S. Block-III, Old MLA Quarters,<br>
                        Hyderguda, Hyderabad - 500029<br>
                        e-mail: tatamadhu@gmail.com
                    </td>
                </tr>
            </table>
        </div>
        """

    formatted_body = (
        final_content.replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("**", "")
        .replace("\n", "<br>")
    )

    canvas_html = f"""<div class="letterhead-container">
{banner_img_html}
<div style="text-align: right; font-weight: 600; font-size: 15px; margin-bottom: 20px; color: #374151;">
స్థలం: {final_location} &nbsp;|&nbsp; తేదీ: {formatted_date}
</div>
<div style="line-height: 1.95; font-size: 18px;">
{formatted_body}
</div>
<div style="border-top: 1.5px dashed #b82329; margin-top: 30px; padding-top: 14px; text-align: right; font-size: 15px; font-weight: 700; color: #374151;">
విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
</div>
</div>"""

    st.markdown(canvas_html, unsafe_allow_html=True)
    
    st.write("")
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        docx_data = create_docx_press_note(final_content, formatted_date, final_location)
        st.download_button(
            label="📄 Word File (.DOCX)",
            data=docx_data,
            file_name=f"Tata_Madhu_PressNote_{formatted_date}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        
    with col_d2:
        html_page = get_printable_letterhead_html(final_content, formatted_date, final_location, lh_banner_base64)
        st.download_button(
            label="🖨️ PDF / Print File (.HTML)",
            data=html_page,
            file_name=f"Tata_Madhu_Letterhead_{formatted_date}.html",
            mime="text/html",
            use_container_width=True,
            help="ఓపెన్ చేసి Print -> Save as PDF ఎంచుకోండి."
        )
        
    with col_d3:
        st.download_button(
            label="📥 Text File (.TXT)",
            data=final_content,
            file_name=f"Tata_Madhu_PressNote_{formatted_date}.txt",
            mime="text/plain",
            use_container_width=True
        )

    st.write("")
    st.subheader("🌐 సోషల్ మీడియా పోస్టులు (Ready to Copy & Paste)")
    
    lines = [line.strip() for line in final_content.split("\n") if line.strip()]
    headline = lines[0] if lines else "ఎమ్మెల్సీ తాతా మధుసూదన్ గారి ప్రకటన"
    for l in lines:
        if "హెడ్" in l or "శీర్షిక" in l or ":" in l:
            headline = l.split(":")[-1].strip()
            break
            
    summary_body = "\n".join(lines[1:5]) if len(lines) > 1 else final_content

    whatsapp_text = f"*{headline}*\n\n{final_content}\n\n_విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం_"
    twitter_text = f"🚨 {headline[:180]}\n\n- ఎమ్మెల్సీ తాతా మధుసూదన్\n\n#TataMadhu #BRSParty #Telangana #Khammam"
    facebook_text = f"📌 {headline}\n\n{final_content}\n\n#TataMadhusudhan #TataMadhu #BRS #Khammam #TelanganaPolitics"
    instagram_text = f"📢 {headline}\n.\n.\n{summary_body[:400]}...\n.\n.\n#TataMadhu #MLCTataMadhu #BRS #Khammam #Telangana #PrajaGontuka"
    youtube_text = f"TITLE:\n{headline} | MLC Tata Madhusudhan Speech\n\nDESCRIPTION:\n{final_content}\n\n#TataMadhu #BRS #TelanganaNews #MLCSpeech"

    st1, st2, st3, st4, st5 = st.tabs(["🟢 WhatsApp", "🔵 Twitter (X)", "🔷 Facebook", "📸 Instagram", "🔴 YouTube"])
    
    with st1:
        st.text_area("WhatsApp Text:", value=whatsapp_text, height=200)
        wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(whatsapp_text[:1400])}"
        st.link_button("📲 వాట్సాప్‌లో షేర్ చేయండి", wa_url, use_container_width=True)
        
    with st2:
        st.text_area("Twitter (X) Post:", value=twitter_text, height=140)
        x_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(twitter_text)}"
        st.link_button("🐦 X (Twitter) లో పోస్ట్ చేయండి", x_url, use_container_width=True)

    with st3:
        st.text_area("Facebook Post:", value=facebook_text, height=200)
        
    with st4:
        st.text_area("Instagram Caption:", value=instagram_text, height=180)

    with st5:
        st.text_area("YouTube Title & Description:", value=youtube_text, height=200)

# Footer Developer Attribution
st.markdown("---")
dev_footer_img = f'<img src="data:image/jpeg;base64,{dev_image_base64}" style="width: 36px; height: 36px; border-radius: 50%; vertical-align: middle; margin-right: 10px; border: 1.5px solid #be123c;">' if dev_image_base64 else '👨‍💻 '
st.markdown(
    f"""
    <div style="text-align: center; color: #374151; font-size: 14px; padding: 18px 0;">
        {dev_footer_img}
        <strong>Designed & Developed by Sumanth Muthamala</strong> &nbsp;|&nbsp; 
        <span style="color: #be123c; font-weight: 600;">Revenue Inspector & PA to MLC Khammam</span>
    </div>
    """, 
    unsafe_allow_html=True
)
