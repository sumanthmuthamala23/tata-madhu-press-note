import os
import time
import json
import base64
import tempfile
import urllib.parse
import requests
import streamlit as st
from google import genai
from google.genai import types

# Page setup
st.set_page_config(
    page_title="MLC తాతా మధు - ప్రెస్ నోట్ జనరేటర్",
    page_icon="📰",
    layout="wide",
)

# Background Image Base64 Converter
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

bg_image_base64 = get_base64_image("background.png")

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

    .press-box {{
        background-color: #ffffff;
        border: 2px solid #b82329;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        color: #111111;
        line-height: 1.9;
        font-size: 18px;
    }}
    
    .press-header {{
        text-align: center;
        border-bottom: 2px dashed #b82329;
        padding-bottom: 16px;
        margin-bottom: 24px;
    }}
    
    .leader-title {{
        color: #dc2626;
        font-size: 30px;
        font-weight: 800;
        margin: 0;
    }}
    
    .party-title {{
        color: #374151;
        font-size: 17px;
        margin-top: 6px;
        font-weight: 600;
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

# 100% Reliable Google Input Tools Transliteration
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

def get_client(api_key: str):
    return genai.Client(api_key=api_key)

# Dynamic resilient generation with automatic model discovery and multi-attempt failover
def generate_press_note_resilient(client: genai.Client, parts: list, occasion: str, location: str):
    prompt_context = (
        f"\nప్రకటన విభాగం / స్వభావం: {occasion}\n"
        f"స్థలం: {location}\n"
        "దయచేసి పైన పేర్కొన్న వివరాలు మరియు అందించిన సమాచారం ఆధారంగా "
        "ఎమ్మెల్సీ తాతా మధుసూదన్ గారి అధికారిక పత్రికా ప్రకటనను రూపొందించండి.\n"
    )
    full_parts = parts + [prompt_context]
    
    # Priority order of available models on modern Gemini API
    candidate_models = [
        "gemini-3.8-flash",
        "gemini-3.8-pro",
        "gemini-3-flash",
        "gemini-2.0-flash",
        "gemini-2.0-pro-exp-02-05"
    ]
    
    # Check valid active models for this API key to avoid 404
    try:
        remote_models = [m.name.replace("models/", "") for m in client.models.list()]
        active_pool = [m for m in candidate_models if m in remote_models]
        if not active_pool:
            # Fallback to any model supporting generation
            active_pool = [m for m in remote_models if "flash" in m or "pro" in m]
    except Exception:
        active_pool = candidate_models

    last_error = None
    for model_name in active_pool:
        # Try up to 2 attempts per model in case of temporary 503 spike
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_parts,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.3,
                    ),
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_error = e
                # Wait 1.5 seconds if 503 occurs before trying again
                time.sleep(1.5)
                continue

    raise last_error

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/BRS_Car_Symbol.png/240px-BRS_Car_Symbol.png", width=80)
    st.title("సెట్టింగ్స్ (Settings)")
    
    default_key = ""
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            default_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    api_key_input = st.text_input(
        "Gemini API Key",
        value=default_key,
        type="password",
        help="Google AI Studio నుండి API Key ఇక్కడ నమోదు చేయండి."
    )
    
    location = st.text_input(
        "స్థలం (Location / Venue)",
        value="హైదరాబాద్ / ఖమ్మం",
        help="స్టేట్‌మెంట్ విడుదల చేసే స్థలం (ఉదా: హైదరాబాద్, ఖమ్మం, శాసనమండలి, ఢిల్లీ)."
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

# ----------------- MAIN UI -----------------
st.title("🎙️ ఎమ్మెల్సీ తాతా మధుసూదన్ - పత్రికా ప్రకటన జనరేటర్")
st.caption("వాయిస్ రికార్డింగ్, ఆడియో/వీడియో లేదా టెక్స్ట్ నోట్స్ ద్వారా మీడియా-రెడీ తెలుగు ప్రెస్ నోట్ రూపొందించండి.")

if not api_key_input:
    st.warning("ముందుగా సైడ్‌బార్‌లో మీ Gemini API Keyని నమోదు చేయండి.")
    st.stop()

try:
    client = get_client(api_key_input)
except Exception as e:
    st.error(f"API Client ఎర్రర్: {str(e)}")
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
                uploaded_ref = client.files.upload(file=tmp_path)
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
        st.error("⚠️ దయచేసి ఆడియో రికార్డ్ చేయండి, ఫైల్ అప్‌లోడ్ చేయండి లేదా నోట్స్ నమోదు చేయండి.")
    else:
        with st.spinner("ఎమ్మెల్సీ గారి అధికారిక ప్రకటన సిద్ధమవుతోంది (Connecting to server)..."):
            try:
                press_note_telugu = generate_press_note_resilient(client, input_parts, selected_scope, location)
                st.session_state["draft_note"] = press_note_telugu
                st.session_state["final_note"] = press_note_telugu
                st.session_state["is_finalized"] = False
            except Exception as e:
                st.error(f"సర్వర్ బిజీగా ఉంది, దయచేసి మరోసారి ప్రయత్నించండి: {str(e)}")

# Display & Edit Section
if "draft_note" in st.session_state:
    st.subheader("✏️ ఎడిట్ & ఫైనలైజ్ చేయండి (Edit & Finalize)")
    
    edited_note = st.text_area(
        "ముసాయిదాను ఇక్కడ పరిశీలించి, అవసరమైన పేర్లు లేదా వివరాలను మార్చుకోండి:",
        value=st.session_state.get("draft_note", ""),
        height=260,
        key="editor_area"
    )
    
    col_d1, col_d2 = st.columns([1, 4])
    with col_d1:
        if st.button("✅ పూర్తయింది (Done / Finalize)", type="primary", use_container_width=True):
            st.session_state["final_note"] = edited_note
            st.session_state["is_finalized"] = True
            st.success("ప్రెస్ నోట్ ఖరారైంది! క్రింద సోషల్ మీడియా విభాగాలలో సిద్ధంగా ఉంది.")

# Official Canvas & Multi-Platform Social Media Hub
if st.session_state.get("is_finalized", False):
    final_content = st.session_state.get("final_note", "")
    
    st.divider()
    st.subheader("📄 అధికారిక ముసాయిదా (Official Letterhead View)")
    
    st.markdown(f"""
    <div class="press-box">
        <div class="press-header">
            <h2 class="leader-title">తాతా మధుసూదన్ (తాతా మధు)</h2>
            <div class="party-title">శాసనమండలి సభ్యులు (Member of Legislative Council - MLC)<br>భారత రాష్ట్ర సమితి (BRS)</div>
        </div>
        <div>
            {final_content.replace(chr(10), '<br>')}
        </div>
        <div style="border-top: 1.5px dashed #dc2626; margin-top: 25px; padding-top: 12px; text-align: right; font-size: 15px; font-weight: 600; color: #4b5563;">
            విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
