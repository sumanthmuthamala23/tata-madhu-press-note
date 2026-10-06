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
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from google import genai
from google.genai import types

# Page setup
st.set_page_config(
    page_title="MLC తాతా మధు - అధికారిక పత్రికా ప్రకటన కన్సోల్",
    page_icon="📰",
    layout="wide",
)

# Helper to read and encode local files to base64
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

bg_image_base64 = get_base64_image("background.png")
dev_image_base64 = get_base64_image("Sumanth.jpg") or get_base64_image("sumanth.jpg")

# Search letterhead file
lh_filename = None
for fname in ["letterhead.png", "letter head(2).jpg", "letterhead.jpg"]:
    if os.path.exists(fname):
        lh_filename = fname
        break
lh_image_base64 = get_base64_image(lh_filename) if lh_filename else None

if bg_image_base64:
    bg_style = f"""
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)),
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
        background: linear-gradient(135deg, #fff5f8 0%, #ffedf2 40%, #ffffff 100%);
        background-attachment: fixed;
    }
    """

# Custom Styling with Anek Telugu Font
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Anek+Telugu:wght@300;400;500;600;700;800&display=swap');
    
    {bg_style}
    
    html, body, [class*="css"], .stMarkdown, p, span, div, input, textarea, button {{
        font-family: 'Anek Telugu', sans-serif !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: rgba(255, 242, 245, 0.96) !important;
        border-right: 1.5px solid #ffccd5;
    }}

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }}

    /* Official Letterhead Container matching A4 */
    .letterhead-container {{
        background-color: #ffffff;
        border: 1.5px solid #e2e8f0;
        border-radius: 6px;
        padding: 30px 48px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        color: #111111;
        line-height: 1.95;
        font-size: 18px;
        max-width: 860px;
        margin: 0 auto;
    }}

    .letterhead-banner-wrapper {{
        width: 100%;
        overflow: hidden;
        max-height: 175px;
        margin-bottom: 20px;
        border-bottom: 2px solid #b82329;
        padding-bottom: 10px;
    }}

    .letterhead-banner-img {{
        width: 100%;
        object-fit: cover;
        object-position: top center;
    }}

    /* Developer Attribution Badge */
    .dev-badge {{
        display: flex;
        align-items: center;
        gap: 12px;
        background: #ffffff;
        border: 1.5px solid #fecdd3;
        border-radius: 12px;
        padding: 10px 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-top: 20px;
    }}
    .dev-img {{
        width: 50px;
        height: 50px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #b82329;
        flex-shrink: 0;
    }}
    .dev-text {{
        font-size: 13px;
        font-weight: 700;
        color: #1f2937;
        line-height: 1.25;
    }}
    .dev-sub {{
        font-size: 11px;
        color: #b82329;
        font-weight: 600;
        margin-top: 3px;
        line-height: 1.3;
    }}
</style>
""", unsafe_allow_html=True)

# ----------------- SYSTEM INSTRUCTION -----------------
SYSTEM_INSTRUCTION = (
    "You are the EXCLUSIVE Chief Media Secretary & Official Telugu Press Spokesperson "
    "for Sri Tata Madhusudhan (Tata Madhu) Garu, Member of Legislative Council (MLC), "
    "Bharat Rashtra Samithi (BRS).\n\n"
    "STRICT CONSTRAINTS:\n"
    "1. LEADER EXCLUSIVITY: Every statement, critique, demand, or declaration must be strictly attributed "
    "to MLC Tata Madhusudhan (శాసనమండలి సభ్యులు తాతా మధుసూదన్ / తాతా మధు). Under no circumstances generate releases for anyone else.\n"
    "2. NO JURISDICTION BOUNDARIES: He speaks on statewide governance, legislative council debates, Hyderabad affairs, national topics, and grassroots public grievances.\n"
    "3. JOURNALISTIC TELUGU: Write in standard high-register journalistic Telugu (ప్రామాణిక పత్రికా భాష) formatted for Telugu daily newspapers (Eenadu, Sakshi, Namasthe Telangana, Andhra Jyothy, etc.).\n"
    "4. STRUCTURE:\n"
    "   - Header: అధికారిక పత్రికా ప్రకటన\n"
    "   - స్థలం & తేదీ\n"
    "   - ప్రధాన శీర్షిక (Impactful headline highlighting 'ఎమ్మెల్సీ తాతా మధు')\n"
    "   - లీడ్ పేరా (Who, What, Where, When, and primary declaration)\n"
    "   - ముఖ్యాంశాలు (3 to 5 clear bulleted points)\n"
    "   - ముగింపు / హెచ్చరిక (Closing remarks and strong political warning)\n"
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

# Resilient Generation with Dynamic Active Model Discovery
def generate_ai_response(keys: list, contents_list: list, system_instruction=SYSTEM_INSTRUCTION, temperature=0.3):
    last_error = None
    for key in keys:
        if not key or not key.strip():
            continue
        try:
            client = genai.Client(api_key=key.strip())
            active_models = []
            try:
                for m in client.models.list():
                    name = m.name.replace("models/", "")
                    methods = getattr(m, "supported_generation_methods", []) or []
                    if not methods or "generateContent" in methods:
                        active_models.append(name)
            except Exception:
                pass
            
            preferred = ["gemini-3.8-flash", "gemini-3.1-pro-preview", "gemini-3-flash", "gemini-2.0-flash"]
            pool = [m for m in preferred if m in active_models]
            for m in active_models:
                if m not in pool and ("flash" in m or "pro" in m):
                    pool.append(m)
            if not pool:
                pool = ["gemini-3.8-flash", "gemini-3.1-pro-preview"]

            for model_name in pool:
                for attempt in range(2):
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
                    except Exception as err:
                        last_error = err
                        time.sleep(1.2)
                        continue
        except Exception as client_err:
            last_error = client_err
            continue
    raise last_error

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
                        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/BRS_Car_Symbol.png/180px-BRS_Car_Symbol.png" width="60" alt="Emblem">
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

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>MLC Tata Madhusudhan Press Note</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Anek+Telugu:wght@400;600;700;800&display=swap');
            body {{
                font-family: 'Anek Telugu', sans-serif;
                background-color: #ffffff;
                margin: 0;
                padding: 40px;
                color: #111;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 10px 20px;
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
            <div class="meta">స్థలం: {location_str} | తేదీ: {date_str}</div>
            <div class="content">
                {content.replace(chr(10), '<br>')}
            </div>
            <div style="border-top: 1px dashed #b82329; margin-top: 35px; padding-top: 12px; text-align: right; font-weight: bold; color: #444;">
                విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
            </div>
        </div>
    </body>
    </html>
    """

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/BRS_Car_Symbol.png/240px-BRS_Car_Symbol.png", width=75)
    st.title("సెట్టింగ్స్ (Settings)")
    
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
    if st.button("🔄 స్థలాన్ని తెలుగులోకి మార్చండి"):
        if loc_eng.strip():
            converted_loc = google_transliterate_telugu(loc_eng)
            st.session_state["final_loc_key"] = converted_loc
            st.rerun()

    final_location = st.text_input(
        "ఫైనల్ స్థలం (Telugu Location):", 
        key="final_loc_key"
    )

    topic_scopes = [
        "ప్రజా సమస్యలు & వినతులు (Public Grievances & Demands)",
        "ప్రభుత్వ విధానాలు / విమర్శలు (State Govt Policies / Criticisms)",
        "రైతాంగ & వ్యవసాయ సమస్యలు (Farmers & Agriculture Issues)",
        "శాసనమండలి ప్రసంగాలు / ప్రశ్నలు (Council Speeches & Legislative Issues)",
        "నియోజకవర్గ అభివృద్ధి & నిధులు (Constituency Development & Sanctions)",
        "పార్టీ కార్యక్రమాలు & సమావేశాలు (Party Meetings & Organizational)",
        "నిరసనలు, ధర్నాలు & పోరాటాలు (Protests & Agitations)",
        "అధికారులతో సమీక్షలు / వినతులు (Official Reviews & Representations)",
        "సేవా కార్యక్రమాలు & సంక్షేమం (Social Welfare & Charity)",
        "శుభాకాంక్షలు & సంతాపాలు (Greetings & Condolences)",
    ]
    selected_scope = st.selectbox("ప్రకటన విభాగం / స్వభావం (Topic Scope)", topic_scopes)

    # Developer Attribution Badge in Sidebar
    st.markdown("---")
    dev_img_html = f'<img src="data:image/jpeg;base64,{dev_image_base64}" class="dev-img">' if dev_image_base64 else '<span style="font-size:24px;">👨‍💻</span>'
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
st.title("🎙️ ఎమ్మెల్సీ తాతా మధుసూదన్ - పత్రికా ప్రకటన జనరేటర్")
st.caption(f"తేదీ: {formatted_date} | స్థలం: {final_location} | అధికారిక లెటర్‌హెడ్ ఫార్మాట్")

if not api_key_input:
    st.warning("ముందుగా సైడ్‌బార్‌లో మీ Gemini API Keyని నమోదు చేయండి.")
    st.stop()

if "final_notes_area" not in st.session_state:
    st.session_state["final_notes_area"] = ""

tab1, tab2, tab3 = st.tabs(["🎤 లైవ్ రికార్డింగ్ (Mic)", "📁 ఆడియో / వీడియో అప్‌లోడ్", "✍️ సిట్యుయేషన్ నోట్స్ (Text)"])

input_parts = []

with tab1:
    st.markdown("##### మైక్ ద్వారా మాట్లాడి రికార్డ్ చేయండి:")
    live_audio = st.audio_input("వాయిస్ రికార్డ్ చేయండి")
    if live_audio:
        st.success("✅ ఆడియో రికార్డ్ అయ్యింది!")
        audio_bytes = live_audio.read()
        input_parts.append(
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        )

with tab2:
    st.markdown("##### ఆడియో లేదా వీడియో ఫైల్ అప్‌లోడ్ చేయండి:")
    uploaded_file = st.file_uploader(
        "సపోర్ట్ ఫార్మాట్లు: MP3, WAV, M4A, MP4", 
        type=["mp3", "wav", "m4a", "mp4"]
    )
    if uploaded_file:
        file_bytes = uploaded_file.read()
        mime_type = uploaded_file.type or "audio/mp3"
        
        if len(file_bytes) > 20 * 1024 * 1024:
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            with st.spinner("ఫైల్ అప్‌లోడ్ అవుతోంది..."):
                c = genai.Client(api_key=active_keys[0])
                uploaded_ref = c.files.upload(file=tmp_path)
                input_parts.append(uploaded_ref)
                os.remove(tmp_path)
        else:
            input_parts.append(
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            )
        st.success(f"✅ {uploaded_file.name} సిద్ధంగా ఉంది.")

with tab3:
    st.markdown("##### ఇంగ్లీష్ ➔ తెలుగు మార్పిడి (English Typing to Telugu):")
    with st.expander("🔤 ఇంగ్లీష్/టాంగ్లీష్‌లో టైప్ చేసి తెలుగులోకి మార్చండి", expanded=True):
        raw_eng = st.text_area(
            "ఇంగ్లీష్ లేదా టాంగ్లీష్ (Tanglish) లో టైప్ చేయండి:",
            placeholder="ఉదాహరణ: Rythu Bandu inka Raledu, Tata Madhu garu mandapaddaru...",
            height=85,
            key="raw_eng_text"
        )
        if st.button("🔄 తెలుగులోకి మార్చండి (Convert to Telugu)"):
            if raw_eng.strip():
                with st.spinner("తెలుగులోకి మారుస్తోంది..."):
                    converted = google_transliterate_telugu(raw_eng)
                    st.session_state["final_notes_area"] = converted
                    st.rerun()
            else:
                st.warning("దయచేసి ఇంగ్లీష్‌లో టెక్స్ట్ టైప్ చేయండి.")

    st.markdown("##### పత్రికా ప్రకటన కోసం ముఖ్యాంశాలు (Notes):")
    notes_text = st.text_area(
        "తెలుగు వివరాలు (నేరుగా ఇక్కడ సవరించుకోవచ్చు):",
        height=140,
        key="final_notes_area"
    )
    if notes_text.strip():
        input_parts.append(types.Part.from_text(text=notes_text))

st.divider()

if st.button("🚀 పత్రికా ప్రకటనను రూపొందించండి (Generate Press Note)", type="primary", use_container_width=True):
    if not input_parts:
        st.error("⚠️ దయచేసి ఆడియో రికార్డ్ చేయండి, ఫైల్ అప్‌‌లోడ్ చేయండి లేదా నోట్స్ నమోదు చేయండి.")
    else:
        with st.spinner("అధికారిక ప్రెస్ నోట్ సిద్ధమవుతోంది..."):
            try:
                prompt_instruction = (
                    f"\nప్రకటన విభాగం / స్వభావం: {selected_scope}\n"
                    f"స్థలం: {final_location}\n"
                    f"తేదీ: {formatted_date}\n"
                    "దయచేసి పైన పేర్కొన్న తేదీ, స్థలం మరియు అందించిన సమాచారం ఆధారంగా "
                    "ఎమ్మెల్సీ తాతా మధుసూదన్ గారి అధికారిక పత్రికా ప్రకటనను రూపొందించండి.\n"
                )
                parts_with_prompt = input_parts + [prompt_instruction]
                press_note_telugu = generate_ai_response(active_keys, parts_with_prompt)
                st.session_state["draft_note"] = press_note_telugu
                st.session_state["final_note"] = press_note_telugu
                st.session_state["is_finalized"] = False
            except Exception as e:
                st.error(f"సర్వర్ బిజీగా ఉంది, దయచేసి మరోసారి ప్రయత్నించండి: {str(e)}")

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
    with st.expander("💡 ప్రెస్ నోట్ మార్పులు (రైతుల ఆవేదన పెంచడం, వివరాలు చేర్చడం, స్పష్టత ఇవ్వడం)", expanded=True):
        ai_remark = st.text_input(
            "మీ సూచన లేదా అభ్యర్థనను ఇక్కడ రాయండి (English or Telugu):",
            placeholder="e.g., 'రైతుల ఆవేదనను మరింత భావోద్వేగంగా మార్చండి', 'Add demand for immediate relief'..."
        )
        if st.button("⚡ సూచన ఆధారంగా ప్రెస్ నోట్ తిరిగి రూపొందించండి (Re-generate with AI)"):
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
    
    if lh_image_base64:
        banner_view = f"""
        <div class="letterhead-banner-wrapper">
            <img src="data:image/png;base64,{lh_image_base64}" class="letterhead-banner-img" alt="Official Letterhead">
        </div>
        """
    else:
        banner_view = """
        <div style="border-bottom: 2px solid #b82329; padding-bottom: 12px; margin-bottom: 20px;">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 40%; vertical-align: top;">
                        <h2 style="color: #b82329; margin: 0; font-size: 22px; font-weight: 800;">TATA MADHUSUDHAN</h2>
                        <div style="font-size: 15px; font-weight: bold;">M.L.C</div>
                        <div style="font-size: 13px; color: #555;">Khammam, Telangana</div>
                    </td>
                    <td style="width: 20%; text-align: center; vertical-align: middle;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/BRS_Car_Symbol.png/180px-BRS_Car_Symbol.png" width="60" alt="Emblem">
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

    st.markdown(f"""
    <div class="letterhead-container">
        {banner_view}
        <div style="text-align: right; font-weight: 600; font-size: 15px; margin-bottom: 20px; color: #374151;">
            స్థలం: {final_location} &nbsp;|&nbsp; తేదీ: {formatted_date}
        </div>
        <div style="line-height: 1.95; font-size: 18px;">
            {final_content.replace(chr(10), '<br>')}
        </div>
        <div style="border-top: 1.5px dashed #b82329; margin-top: 30px; padding-top: 14px; text-align: right; font-size: 15px; font-weight: 700; color: #374151;">
            విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Direct Downloads
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
        html_page = get_printable_letterhead_html(final_content, formatted_date, final_location, lh_image_base64)
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
dev_footer_img = f'<img src="data:image/jpeg;base64,{dev_image_base64}" style="width: 36px; height: 36px; border-radius: 50%; vertical-align: middle; margin-right: 10px; border: 1.5px solid #b82329;">' if dev_image_base64 else '👨‍💻 '
st.markdown(
    f"""
    <div style="text-align: center; color: #374151; font-size: 14px; padding: 18px 0;">
        {dev_footer_img}
        <strong>Designed & Developed by Sumanth Muthamala</strong> &nbsp;|&nbsp; 
        <span style="color: #b82329; font-weight: 600;">Revenue Inspector & PA to MLC Khammam</span>
    </div>
    """, 
    unsafe_allow_html=True
)
