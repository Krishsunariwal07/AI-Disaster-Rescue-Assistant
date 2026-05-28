# ================= IMPORTS =================

import streamlit as st
from google import genai
import emergency_data
import utils
import requests
import tempfile
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from streamlit_folium import st_folium
from gtts import gTTS
from fpdf import FPDF
from PIL import Image

from streamlit_js_eval import get_geolocation


# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="🚨 AI Disaster Rescue Assistant",
    layout="wide"
)


# ================= CUSTOM UI =================

st.markdown("""
<style>

.stApp {
    background-color: #0f1117;
    color: white;
}

h1 {
    color: #ff4b4b;
    text-align: center;
}

.stButton>button {
    background-color: #ff4b4b;
    color: white;
    border-radius: 12px;
    height: 50px;
    width: 100%;
    font-size: 18px;
    font-weight: bold;
}

.stTextInput>div>div>input {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# ================= SESSION STATE =================

if "response" not in st.session_state:
    st.session_state.response = ""

if "map" not in st.session_state:
    st.session_state.map = None

if "hospitals" not in st.session_state:
    st.session_state.hospitals = []

if "sos" not in st.session_state:
    st.session_state.sos = ""

if "risk" not in st.session_state:
    st.session_state.risk = ""


# ================= GEMINI =================

client = genai.Client(
    api_key="AIzaSyB9vlFwCUM8B5HnWE7D8QHa9KOxELIrkuk"
)


# ================= WEATHER =================

def get_weather(city):

    try:

        api_key = "AIzaSyB9vlFwCUM8B5HnWE7D8QHa9KOxELIrkuk"

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        response = requests.get(url)

        return response.json()

    except:

        return None


# ================= RISK LEVEL =================

def get_risk_level(query):

    query = query.lower()

    if any(word in query for word in [
        "earthquake",
        "explosion",
        "cyclone"
    ]):
        return "🔴 CRITICAL"

    elif any(word in query for word in [
        "fire",
        "flood",
        "accident"
    ]):
        return "🟠 HIGH"

    else:
        return "🟢 MEDIUM"


# ================= PDF REPORT =================

def generate_pdf(text):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):

        pdf.multi_cell(0, 10, line)

    pdf.output("emergency_report.pdf")


# ================= EMAIL SOS =================

def send_email_sos(receiver, message):

    try:

        sender_email = "YOUR_EMAIL@gmail.com"
        sender_password = "YOUR_APP_PASSWORD"

        msg = MIMEMultipart()

        msg["From"] = sender_email
        msg["To"] = receiver
        msg["Subject"] = "🚨 Emergency SOS Alert"

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            sender_email,
            sender_password
        )

        server.send_message(msg)

        server.quit()

        return True

    except:

        return False


# ================= TITLE =================

st.title("🚨 AI Disaster Rescue Assistant")

st.markdown(
    "### AI Powered Emergency & Disaster Management System"
)


# ================= SIDEBAR =================

with st.sidebar:

    st.header("⚡ Emergency Contacts")

    st.success("🚑 Ambulance: 108")

    st.error("🚓 Police: 100")

    st.warning("🔥 Fire Brigade: 101")

    st.info("🌊 Disaster Helpline: 1070")


# ================= LANGUAGE =================

language_option = st.selectbox(
    "🌎 Choose Language",
    ["English", "Hindi"]
)

if language_option == "English":
    lang = "en"
else:
    lang = "hi"


# ================= GPS =================

st.subheader("📍 Live GPS Location")

location_data = get_geolocation()

if location_data:

    st.success("GPS Location Detected")

    st.write(location_data)


# ================= INPUT =================

query = st.text_input(
    "🚨 Enter Emergency",
    placeholder="Example: flood in indore"
)


# ================= IMAGE =================

uploaded = st.file_uploader(
    "📸 Upload Disaster Image",
    type=["png", "jpg", "jpeg"]
)

if uploaded:

    image = Image.open(uploaded)

    st.image(image, width=400)

    st.success("✅ Image Uploaded")

    # ================= GEMINI IMAGE ANALYSIS =================

    try:

        prompt = """
        Analyze this disaster image.
        Tell:
        1. Disaster type
        2. Severity
        3. Safety precautions
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, image]
        )

        st.subheader("📸 AI Image Analysis")

        st.write(response.text)

    except:

        st.warning("Image AI unavailable")


# ================= CHAT =================

chat = st.chat_input(
    "💬 Ask Emergency AI"
)

if chat:

    query = chat


# ================= ANALYZE =================

if st.button("🚨 Analyze Emergency"):

    with st.spinner("Analyzing Emergency..."):

        # ================= RISK =================

        risk = get_risk_level(query)

        st.session_state.risk = risk

        # ================= AI RESPONSE =================

        try:

            prompt = f"""
            Emergency: {query}

            Give:
            1. Safety precautions
            2. Emergency checklist
            3. SOS message
            4. Survival tips
            5. Nearby help suggestions
            6. Evacuation advice

            Language: {lang}
            """

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            st.session_state.response = response.text

        except Exception:

            found = False

            for key in emergency_data.OFFLINE_SAFETY_DATA:

                if key in query.lower():

                    data = emergency_data.OFFLINE_SAFETY_DATA[key][lang]

                    output = f"## {data['title']}\n\n"

                    for step in data["steps"]:
                        output += f"✅ {step}\n\n"

                    for item in data["checklist"]:
                        output += f"📌 {item}\n\n"

                    st.session_state.response = output

                    found = True

            if not found:

                st.session_state.response = (
                    emergency_data.DEFAULT_ADVICE[lang]
                )

        # ================= LOCATION =================

        location = query.lower()

        words = [
            "flood in",
            "fire in",
            "earthquake in",
            "cyclone in",
            "accident in"
        ]

        for word in words:

            location = location.replace(word, "")

        location = location.strip()

        # ================= HOSPITALS =================

        lat, lon = utils.get_coordinates(location)

        if lat and lon:

            hospitals = utils.get_nearby_hospitals(
                lat,
                lon
            )

            st.session_state.hospitals = hospitals

            map_obj = utils.create_map(
                lat,
                lon,
                hospitals
            )

            st.session_state.map = map_obj

        # ================= SOS =================

        st.session_state.sos = f"""
HELP!

Emergency:
{query}

Need immediate assistance.

Location:
{location}
"""


# ================= AI RESPONSE =================

if st.session_state.response:

    st.subheader("🤖 AI Guidance")

    st.write(st.session_state.response)


# ================= RISK =================

if st.session_state.risk:

    st.subheader("⚠ Risk Level")

    st.error(st.session_state.risk)


# ================= VOICE =================

if st.session_state.response:

    try:

        tts = gTTS(st.session_state.response)

        tts.save("voice.mp3")

        audio = open("voice.mp3", "rb")

        st.audio(audio.read())

    except:

        st.warning("Voice unavailable")


# ================= WEATHER =================

if query:

    location = query.lower()

    for word in [
        "flood in",
        "fire in",
        "earthquake in",
        "cyclone in"
    ]:

        location = location.replace(word, "")

    location = location.strip()

    weather = get_weather(location)

    if weather and "main" in weather:

        st.subheader("🌦 Live Weather")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "🌡 Temperature",
                f"{weather['main']['temp']} °C"
            )

        with col2:
            st.metric(
                "💨 Wind Speed",
                weather["wind"]["speed"]
            )

        with col3:
            st.metric(
                "☁ Weather",
                weather["weather"][0]["description"]
            )


# ================= HOSPITALS =================

if st.session_state.hospitals:

    st.subheader("🏥 Nearby Hospitals")

    for hospital in st.session_state.hospitals[:5]:

        st.success(hospital["name"])


# ================= MAP =================

if st.session_state.map:

    st.subheader("🗺 Emergency Map")

    st_folium(
        st.session_state.map,
        width=1000,
        height=500
    )


# ================= SOS =================

if st.session_state.sos:

    st.subheader("🚨 SOS Message")

    st.code(st.session_state.sos)

    st.download_button(
        "⬇ Download SOS",
        st.session_state.sos,
        file_name="sos_message.txt"
    )

    whatsapp_url = (
        f"https://wa.me/?text={st.session_state.sos}"
    )

    st.link_button(
        "📲 Send WhatsApp SOS",
        whatsapp_url
    )


# ================= EMAIL SOS =================

st.subheader("📧 Send SOS Email")

receiver_email = st.text_input(
    "Enter Receiver Email"
)

if st.button("📧 Send Email SOS"):

    success = send_email_sos(
        receiver_email,
        st.session_state.sos
    )

    if success:

        st.success("SOS Email Sent")

    else:

        st.error("Failed to Send Email")


# ================= PDF =================

if st.session_state.response:

    generate_pdf(st.session_state.response)

    pdf_file = open(
        "emergency_report.pdf",
        "rb"
    )

    st.download_button(
        "📄 Download Emergency PDF",
        pdf_file,
        file_name="emergency_report.pdf"
    )


# ================= CONTACTS =================

st.subheader("☎ Emergency Contacts")

col1, col2, col3 = st.columns(3)

with col1:
    st.error("🚓 Police\n\n100")

with col2:
    st.success("🚑 Ambulance\n\n108")

with col3:
    st.warning("🔥 Fire Brigade\n\n101")


# ================= SURVIVAL TIPS =================

st.subheader("🛡 Survival Tips")

tips = [
    "Carry water and medicines",
    "Keep phone charged",
    "Avoid panic",
    "Stay connected to authorities",
    "Use emergency kits",
    "Stay indoors during severe storms",
    "Keep emergency contacts ready"
]

for tip in tips:

    st.write("✅", tip)


# ================= FOOTER =================

st.markdown("---")

st.caption(
    "🚨 AI Disaster Rescue Assistant | Powered by Gemini AI"
)