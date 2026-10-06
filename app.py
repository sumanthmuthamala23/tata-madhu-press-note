import os
import base64
import tempfile
import urllib.parse
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

    /* Official Press Note Container */
    .press-box {{
        background-color: #ffffff;
        border: 2px solid #b82329;
        border-radius: 12px;
        padding: 32px;
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
SYSTEM_INSTRUCTION = """
You are the EXCLUSIVE Chief Media Secretary & Official Telugu Press Spokesperson for Sri Tata Madhusudhan (Tata Madhu) Garu.
- Designation: Member of Legislative Council (MLC), Bharat Rashtra Samithi (BRS).
- Voice & Tone: Senior legislative leader representing the public interest, authoritative, articulate, and politically assertive.

STRICT CONSTRAINTS:
1. LEADER EXCLUSIVITY: Every statement, critique, demand, or declaration must be strictly attributed to MLC Tata Madhusudhan (శాసనమండలి సభ్యులు తాతా మధుసూదన్ / తాతా మధు).
2. NO JURISDICTION BOUNDARIES: Do not limit him to any single district. He issues statements on state policies, legislative council debates, Hyderabad affairs, national topics, and grassroots public grievances.
3. STANDARD JOURNALISTIC TELUGU: Write in high-standard news Telugu (ప్రామాణిక పత్రికా భాష) formatted for Telugu daily newspapers (Eenadu, Sakshi, Namasthe Telangana, Andhra Jyothy, etc.).
4. STRUCTURE:
   - Header: అధికారిక పత్రికా ప్రకటన
   - స్థలం & తేదీ
   - ప్రధాన శీర్షిక (Impactful headline highlighting 'ఎమ్మెల్సీ తాతా మధు')
   - లీడ్ పేరా (Who, What, Where, When, and primary declaration)
   - ముఖ్యాంశాలు (3-5 bulleted points)
   - ముగింపు / హెచ్చరిక (Closing remarks and strong political warning)
   - విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
"""

def get_client(api_key: str):
    return genai.Client(api_key=api_key)

# Dynamic Model Resolver: Checks which models exist on your key to prevent 404 forever
@st.cache_data(show_spinner=False, ttl=3600)
def resolve_best_model(_client: genai.Client):
    # Candidate list in priority order
    preferred = [
        "gemini-3.8-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
    ]
    try:
        available_models = [m.name.replace("models/", "") for m in _client.models.list()]
        for p in preferred:
            if p in available_models:
                return p
        # If none of preferred matched, pick any available flash or general model
        flash_models = [m for m in available_models if "flash" in m]
        if flash_models:
            return flash_models[0]
        return available_models[0]
    except Exception:
        # Safe default
        return "gemini-3.8-flash"

def generate_safe_content(client: genai.Client, contents, system_instruction=None, temperature=0.3):
    model_name = resolve_best_model(client)
    
    config = types.GenerateContentConfig(
        temperature=temperature,
    )
    if system_instruction:
        config.system_instruction = system_instruction
        
    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config,
    )
    return response.text

# English to Telugu Transliteration Function
def transliterate_to_telugu(client: genai.Client, english_text: str):
    prompt = f"""
    Translate and transliterate this English/Tanglish phonetic text into standard, grammatically correct Telugu script:
    "{english_text}"
    
    Rules:
    - Output ONLY the clean Telugu script text.
    - No English words unless they are proper technical/designation terms.
    - No explanations or additional commentary.
    """
    return generate_safe_content(client, contents=prompt, temperature=0.1)

# Press Note Generation Function
def generate_press_note(client: genai.Client, parts: list, occasion: str, location: str):
    prompt_context = f"""
    ప్రకటన విభాగం / స్వభావం: {occasion}
    స్థలం: {location}
    దయచేసి పైన పేర్కొన్న వివరాలు మరియు అందించిన సమాచారం ఆధారంగా ఎమ్మెల్సీ తాతా మధుసూదన్ గారి అధికారిక పత్రికా ప్రకటనను రూపొందించండి.
    """
    parts.append(prompt_context)
    return generate_safe_content(client, contents=parts, system_instruction=SYSTEM_INSTRUCTION, temperature=0.3)

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

if "telugu_notes" not in st.session_state:
    st.session_state["telugu_notes"] = ""

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
            placeholder="ఉదాహరణ: rythu bandu inka raledu, Tata Madhu garu mandapaddaru...",
            height=80,
            key="raw_eng_text"
        )
        if st.button("🔄 తెలుగులోకి మార్చండి (Convert to Telugu)"):
            if raw_eng.strip():
                with st.spinner("తెలుగులోకి మారుస్తోంది..."):
                    try:
                        telugu_converted = transliterate_to_telugu(client, raw_eng)
                        st.session_state["telugu_notes"] = telugu_converted.strip()
                        st.success("✅ విజయవంతంగా తెలుగులోకి మారింది!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"మార్పిడి ఎర్రర్: {str(err)}")
            else:
                st.warning("దయచేసి ఇంగ్లీష్‌లో టెక్స్ట్ టైప్ చేయండి.")

    st.markdown("##### పత్రికా ప్రకటన కోసం ముఖ్యాంశాలు (Notes):")
    notes_text = st.text_area(
        "తెలుగు వివరాలు (నేరుగా ఇక్కడ సవరించుకోవచ్చు):",
        value=st.session_state["telugu_notes"],
        height=130,
        key="final_notes_area"
    )
    if notes_text.strip():
        input_parts.append(types.Part.from_text(text=notes_text))

st.divider()

if st.button("🚀 పత్రికా ప్రకటనను రూపొందించండి (Generate Press Note)", type="primary", use_container_width=True):
    if not input_parts:
        st.error("⚠️ దయచేసి ఆడియో రికార్డ్ చేయండి, ఫైల్ అప్‌లోడ్ చేయండి లేదా నోట్స్ నమోదు చేయండి.")
    else:
        with st.spinner("ఎమ్మెల్సీ గారి అధికారిక ప్రకటన సిద్ధమవుతోంది..."):
            try:
                press_note_telugu = generate_press_note(client, input_parts, selected_scope, location)
                st.session_state["generated_note"] = press_note_telugu
            except Exception as e:
                st.error(f"ఎర్రర్ సంభవించింది: {str(e)}")

# Display Result
if "generated_note" in st.session_state:
    st.subheader("📄 అధికారిక ముసాయిదా (Official Press Release)")
    
    st.markdown(f"""
    <div class="press-box">
        <div class="press-header">
            <h2 class="leader-title">తాతా మధుసూదన్ (తాతా మధు)</h2>
            <div class="party-title">శాసనమండలి సభ్యులు (Member of Legislative Council - MLC)<br>భారత రాష్ట్ర సమితి (BRS)</div>
        </div>
        <div>
            {st.session_state["generated_note"].replace(chr(10), '<br>')}
        </div>
        <div style="border-top: 1.5px dashed #dc2626; margin-top: 25px; padding-top: 12px; text-align: right; font-size: 15px; font-weight: 600; color: #4b5563;">
            విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 టెక్స్ట్ ఫైల్‌గా డౌన్‌లోడ్ చేయండి",
            data=st.session_state["generated_note"],
            file_name=f"Tata_Madhu_Press_Note_{location.split()[0]}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        encoded_note = st.session_state["generated_note"][:1200]
        wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(encoded_note)}"
        st.link_button("📲 వాట్సాప్‌లో షేర్ చేయండి", wa_url, use_container_width=True)
