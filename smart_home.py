import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
import speech_recognition as sr
import pyttsx3
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Smart Home Simulation Create By Prathmesh", layout="wide")

USER_FILE = "users.csv"

# ---------------- USER SYSTEM ----------------
def load_users():
    if os.path.exists(USER_FILE):
        try:
            df = pd.read_csv(USER_FILE, dtype=str).fillna("")
            df["username"] = df["username"].str.strip().str.lower()
            df["password"] = df["password"].str.strip()
            return df
        except Exception:
            return pd.DataFrame(columns=["username", "password"])
    else:
        df = pd.DataFrame(columns=["username", "password"])
        df.to_csv(USER_FILE, index=False)
        return df


def save_user(username, password):
    username = username.strip().lower()
    password = password.strip()
    df = load_users()
    if username in df["username"].values:
        return False
    df = pd.concat([df, pd.DataFrame([{"username": username, "password": password}])], ignore_index=True)
    df.to_csv(USER_FILE, index=False)
    return True


def validate_user(username, password):
    username = username.strip().lower()
    password = password.strip()
    df = load_users()
    match = df[(df["username"] == username) & (df["password"] == password)]
    return not match.empty


# ---------------- UTILITIES ----------------
def init_session():
    defaults = {
        "logged_in": False,
        "username": "",
        "devices": {"Light": False, "Fan": False, "AC": False, "TV": False},
        "automation": {"room_auto": True, "temp_threshold_ac": 30},
        "last_log_update": datetime.now() - timedelta(hours=1)
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if "engine" not in st.session_state:
        try:
            st.session_state.engine = pyttsx3.init()
        except Exception:
            st.session_state.engine = None


def tts_say(text):
    engine = st.session_state.get("engine")
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass


def get_user_log_file():
    """Return log file path based on username"""
    if st.session_state.get("username"):
        return f"device_log_{st.session_state.username}.csv"
    return "device_log.csv"


def save_log(total_power):
    """Save logs only once every 1 hour per user"""
    log_file = get_user_log_file()
    now = datetime.now()
    if now - st.session_state.last_log_update >= timedelta(hours=1):
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        row = {"Time": timestamp, "Total Power": total_power}

        if os.path.exists(log_file):
            df = pd.read_csv(log_file)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        df.to_csv(log_file, index=False)
        st.session_state.last_log_update = now
        st.toast("🕒 Log updated for this hour!")


def read_logs(n=10):
    """Read latest n logs for the current user"""
    log_file = get_user_log_file()
    if os.path.exists(log_file):
        df = pd.read_csv(log_file)
        return df.tail(n).reset_index(drop=True)
    return pd.DataFrame(columns=["Time", "Total Power"])


def simulate_power_usage(devices):
    return {d: random.randint(50, 300) if s else 0 for d, s in devices.items()}


def simulate_room_temperature():
    return random.uniform(18, 40)


def room_temp_automation(temp):
    threshold = st.session_state.automation["temp_threshold_ac"]
    if st.session_state.automation["room_auto"]:
        if temp >= threshold and not st.session_state.devices["AC"]:
            st.session_state.devices["AC"] = True
            tts_say("Room temperature high. AC turned on.")
        elif temp < threshold and st.session_state.devices["AC"]:
            st.session_state.devices["AC"] = False
            tts_say("Room temperature normal. AC turned off.")


# ---------------- APP START ----------------
init_session()


def safe_rerun():
    try:
        st.rerun()
    except Exception:
        pass


# ---------- LOGIN / SIGNUP ----------
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center'>AI Smart Home Simulation</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray'>IoT simulation with voice control and automation.</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if validate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                tts_say(f"Welcome {username}")
                st.success(f"Welcome, {username.capitalize()}!")
                safe_rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        new_user = st.text_input("New Username", key="signup_user")
        new_pass = st.text_input("New Password", type="password", key="signup_pass")
        if st.button("Create Account"):
            if new_user and new_pass:
                if save_user(new_user, new_pass):
                    st.success("Account created successfully! Logging you in...")
                    tts_say("Account created successfully. Welcome!")
                    st.session_state.logged_in = True
                    st.session_state.username = new_user
                    safe_rerun()
                else:
                    st.warning("Username already exists! Try another.")
            else:
                st.error("Please fill in all fields.")
    st.stop()


# ---------- MAIN DASHBOARD ----------
st.markdown(
    """
    <div style="text-align:center; padding:10px 0;">
        <h1>AI Smart Home Dashboard</h1>
        <p style="color:gray;">Monitor • Automate • Control</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.title(f"Hello, {st.session_state.username.capitalize()}")
st.sidebar.markdown("**Controls & Settings**")

# Auto-refresh every 5 seconds (UI only)
st_autorefresh(interval=5000, key="ui_refresh")

# Automation settings
st.sidebar.subheader("Automation Settings")
room_auto = st.sidebar.checkbox("Enable temperature-based automation", value=st.session_state.automation["room_auto"])
st.session_state.automation["room_auto"] = room_auto
temp_thresh = st.sidebar.number_input("AC temperature threshold (°C)", min_value=16, max_value=45, value=st.session_state.automation["temp_threshold_ac"])
st.session_state.automation["temp_threshold_ac"] = temp_thresh

# Simulate temperature
room_temp = simulate_room_temperature()
st.metric("Room Temperature (°C)", f"{room_temp:.1f}")
room_temp_automation(room_temp)

# Device Control
st.header("Device Control")
cols = st.columns(4)
for i, device in enumerate(st.session_state.devices.keys()):
    with cols[i]:
        st.session_state.devices[device] = st.toggle(device, value=st.session_state.devices[device])

# Commands
st.header("Voice / Text Commands")
st.markdown("Try commands like: `turn on light`, `turn off fan`, or `status`")
voice_col, text_col = st.columns(2)

with voice_col:
    if st.button("Start Voice Command"):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                st.info("Listening... speak now.")
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
            cmd = r.recognize_google(audio).lower()
            st.success(f"You said: {cmd}")
            for d in st.session_state.devices:
                if d.lower() in cmd:
                    if "on" in cmd:
                        st.session_state.devices[d] = True
                        tts_say(f"Turning on {d}")
                    elif "off" in cmd:
                        st.session_state.devices[d] = False
                        tts_say(f"Turning off {d}")
            if "status" in cmd:
                status = ", ".join([f"{k}: {'ON' if v else 'OFF'}" for k, v in st.session_state.devices.items()])
                st.info(status)
                tts_say("Showing current device status.")
        except Exception:
            st.error("Voice recognition failed or mic not available.")

with text_col:
    typed = st.text_input("Type command and press Enter")
    if typed:
        cmd = typed.lower()
        for d in st.session_state.devices:
            if d.lower() in cmd:
                if "on" in cmd:
                    st.session_state.devices[d] = True
                    st.success(f"{d} turned ON")
                    tts_say(f"{d} is now on")
                elif "off" in cmd:
                    st.session_state.devices[d] = False
                    st.success(f"{d} turned OFF")
                    tts_say(f"{d} is now off")
        if "status" in cmd:
            status = "\n".join([f"{k}: {'ON' if v else 'OFF'}" for k, v in st.session_state.devices.items()])
            st.info(status)
            tts_say("Displayed device status.")

# Energy Usage
st.header("Energy Usage")
usage = simulate_power_usage(st.session_state.devices)
df_usage = pd.DataFrame(list(usage.items()), columns=["Device", "Power (W)"])
total_power = df_usage["Power (W)"].sum()
st.dataframe(df_usage, use_container_width=True)
st.metric("Total Power (W)", total_power)

fig, ax = plt.subplots()
ax.bar(df_usage["Device"], df_usage["Power (W)"])
ax.set_ylim(0, 350)
ax.set_ylabel("Watts")
ax.set_title("Energy Usage per Device")
st.pyplot(fig)

# Save logs only once/hour
save_log(total_power)

# Show recent logs
st.subheader("Recent Logs")
st.dataframe(read_logs(8), use_container_width=True)
next_update = st.session_state.last_log_update + timedelta(hours=1)
st.info(f"Next log update at: {next_update.strftime('%H:%M:%S')}")

# Logout button
st.sidebar.write("---")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    safe_rerun()
