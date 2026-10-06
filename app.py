import os
import tempfile
import urllib.parse
import streamlit as st
from google import genai
from google.genai import types

# Page setup
st.set_page_config(
    page_title="తాతా మధు - ప్రెస్ నోట్ జనరేటర్",
    page_icon="📰",
    layout="wide",
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Suranna&display=swap');
    
    .press-box {
        background-color: #ffffff;
        border: 2px solid #b82329;
        border-radius: 8px;
        padding: 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
        color: #111111;
        line-height: 1.8;
        font-family: 'Suranna', serif;
    }
    .press-header {
        text-align: center;
        border-bottom: 2px dashed #b82329;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }
    .leader-title {
        color: #dc2626;
        font-size: 26px;
        font-weight: 700;
        margin: 0;
    }
    .party-title {
        color: #374151;
        font-size: 15px;
        margin-top: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

SYSTEM_INSTRUCTION = """
You are the Chief Media Secretary & Official Telugu Spokesperson for Sri Tata Madhusudhan (Tata Madhu) Garu,
Member of Legislative Council (MLC), Khammam Local Authorities Constituency, Bharat Rashtra Samithi (BRS).

OBJECTIVE:
Analyze multimodal media (audio recording, video, or situation notes) and draft an authentic, 
journalistic, and authoritative Telugu Press Release (పత్రికా ప్రకటన) ready for distribution to Telugu media 
(Eenadu, Sakshi, Namasthe Telangana, Andhra Jyothy, Prajasakti, TV9, T News, etc.).

LEADER PROTOCOL:
- Full Designation: శాసనమండలి సభ్యులు (MLC), బీఆర్ఎస్ ఖమ్మం జిల్లా అధ్యక్షుడు తాతా మధుసూదన్ (తాతా మధు) గారు.
- Voice/Tone: Direct, authoritative, fighting for public issues, critical of anti-people policies.

FORMAT REQUIRED:
1. Header: అధికారిక పత్రికా ప్రకటన (Official Press Release)
2. స్థలం & తేదీ (Place and Date)
3. ప్రధాన శీర్షిక (Impactful headline typical of Telugu dailies)
4. లీడ్ పేరా (Opening Paragraph covering Who, What, Where, When, and the primary declaration)
5. ముఖ్యాంశాలు (Key Bullet Points highlighting exact demands, ground reality, or political stance)
6. ముగింపు / హెచ్చరిక (Closing remarks, direct quotations, or warning to authorities)
7. విడుదల (Issued by): ఎమ్మెల్సీ కార్యాలయం, ఖమ్మం.

RULES:
- Maintain high-register journalistic Telugu (ప్రామాణిక పత్రికా భాష).
- Strictly adhere to factual points provided in the audio/text without fabricating false incidents.
- If audio has background noise or slurred speech, extract the central political arguments accurately.
"""

def get_client(api_key: str):
    return genai.Client(api_key=api_key)

def generate_press_note(client: genai.Client, parts: list, occasion: str, location: str):
    prompt_context = f"""
    సందర్భం (Occasion): {occasion}
    ప్రాంతం (Location): {location}
    దయచేసి పైన పేర్కొన్న వివరాలు మరియు అందించిన ఆడియో/వీడియో/నోట్స్ ఆధారంగా అధికారిక తెలుగు పత్రికా ప్రకటనను రూపొందించండి.
    """
    parts.append(prompt_context)
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
        ),
    )
    return response.text

# --- Sidebar ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/BRS_Car_Symbol.png/240px-BRS_Car_Symbol.png", width=80)
    st.title("సెట్టింగ్స్ (Settings)")
    
    # Priority: Secrets first, then sidebar input
    default_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
    api_key_input = st.text_input(
        "Gemini API Key",
        value=default_key,
        type="password",
        help="Google AI Studio నుండి తీసుకున్న API Keyని ఇక్కడ ఎంటర్ చేయండి."
    )
    
    occasion = st.selectbox(
        "కార్యక్రమం / సందర్భం",
        [
            "మీడియా సమావేశం (Press Meet)",
            "వరదలు / విపత్తుల పర్యటన (Flood / Disaster Inspection)",
            "ప్రజా సమస్యలపై నిరసన (Protest / Counter Attack)",
            "నియోజకవర్గ అభివృద్ధి సమీక్ష (Development Review)",
            "రైతు సమస్యలు (Farmers / Agricultural Issues)",
            "సంతాపం / శుభాకాంక్షలు (Condolence / Greetings)"
        ]
    )
    
    location = st.text_input("స్థలం (Location)", value="ఖమ్మం (Khammam)")

# --- Main UI ---
st.title("🎙️ MLC తాతా మధుసూదన్ - పత్రికా ప్రకటన జనరేటర్")
st.caption("వాయిస్ రికార్డింగ్, ఆడియో/వీడియో లేదా టెక్స్ట్ నోట్స్ ద్వారా మీడియా-రెడీ ప్రెస్ నోట్ రూపొందించండి.")

if not api_key_input:
    st.info("👈 దయచేసి ఎడమవైపు సైడ్‌బార్‌లో మీ Gemini API Keyని నమోదు చేయండి.")
    st.stop()

client = get_client(api_key_input)

tab1, tab2, tab3 = st.tabs(["🎤 లైవ్ రికార్డింగ్ (Mic)", "📁 ఆడియో / వీడియో అప్‌లోడ్", "✍️ సిట్యుయేషన్ నోట్స్ (Text)"])

input_parts = []

with tab1:
    st.markdown("##### మీ ఫోన్ లేదా మైక్ ద్వారా నేరుగా మాట్లాడి రికార్డ్ చేయండి:")
    live_audio = st.audio_input("వాయిస్ రికార్డ్ చేయండి")
    if live_audio:
        st.success("✅ ఆడియో విజయవంతంగా రికార్డ్ అయ్యింది!")
        audio_bytes = live_audio.read()
        input_parts.append(
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        )

with tab2:
    st.markdown("##### రికార్డ్ చేసిన ఆడియో లేదా వీడియో ఫైల్ అప్‌లోడ్ చేయండి:")
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
            with st.spinner("పెద్ద ఫైల్ అప్‌లోడ్ అవుతోంది..."):
                uploaded_ref = client.files.upload(file=tmp_path)
                input_parts.append(uploaded_ref)
                os.remove(tmp_path)
        else:
            input_parts.append(
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            )
        st.success(f"✅ {uploaded_file.name} సిద్ధంగా ఉంది.")

with tab3:
    st.markdown("##### సందర్భం లేదా ముఖ్యమైన పాయింట్లు టైప్ చేయండి:")
    notes_text = st.text_area(
        "వివరాలు / పాయింట్లు",
        placeholder="ఉదాహరణ: ఖమ్మం మున్నేరు వరద బాధితులను పరామర్శించిన తాతా మధు గారు. సహాయక చర్యల్లో అధికారులు విఫలమయ్యారని ధ్వజమెత్తారు...",
        height=140
    )
    if notes_text.strip():
        input_parts.append(types.Part.from_text(text=notes_text))

st.divider()

if st.button("🚀 పత్రికా ప్రకటనను రూపొందించండి (Generate Press Note)", type="primary", use_container_width=True):
    if not input_parts:
        st.error("⚠️ దయచేసి ఏదైనా ఆడియో రికార్డ్ చేయండి, ఫైల్ అప్‌లోడ్ చేయండి లేదా నోట్స్ టైప్ చేయండి.")
    else:
        with st.spinner("ఎమ్మెల్సీ గారి పత్రికా ప్రకటన సిద్ధమవుతోంది..."):
            try:
                press_note_telugu = generate_press_note(client, input_parts, occasion, location)
                st.session_state["generated_note"] = press_note_telugu
            except Exception as e:
                st.error(f"ఎర్రర్ సంభవించింది: {str(e)}")

# Display Generated Note
if "generated_note" in st.session_state:
    st.subheader("📄 అధికారిక ముసాయిదా (Official Draft)")
    
    st.markdown(f"""
    <div class="press-box">
        <div class="press-header">
            <h2 class="leader-title">తాతా మధుసూదన్ (తాతా మధు)</h2>
            <div class="party-title">శాసనమండలి సభ్యులు (MLC) | ఖమ్మం స్థానిక సంస్థల నియోజకవర్గం<br>బీఆర్ఎస్ ఖమ్మం జిల్లా అధ్యక్షులు</div>
        </div>
        <div>
            {st.session_state["generated_note"].replace('\n', '<br>')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 టెక్స్ట్ ఫైల్‌గా డౌన్‌లోడ్ చేయండి",
            data=st.session_state["generated_note"],
            file_name=f"Tata_Madhu_Press_Note_{location}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        encoded_note = st.session_state["generated_note"][:1200]
        wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(encoded_note)}"
        st.link_button("📲 వాట్సాప్‌లో షేర్ చేయండి", wa_url, use_container_width=True)
