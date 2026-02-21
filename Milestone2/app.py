import streamlit as st
import sqlite3
import jwt
import datetime
import random
import smtplib
from email.message import EmailMessage

# ----------------- CONFIG -----------------
SECRET_KEY = "policynav_secret"

# ----------------- DB -----------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT,
    email TEXT PRIMARY KEY,
    password TEXT,
    question TEXT,
    answer TEXT
)
""")
conn.commit()

# ----------------- OTP EMAIL -----------------
def send_otp(email, otp):
    msg = EmailMessage()
    msg.set_content(f"Your OTP for PolicyNav login is: {otp}")
    msg["Subject"] = "PolicyNav OTP Verification"
    msg["From"] = st.secrets["EMAIL_ID"]
    msg["To"] = email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(
        st.secrets["EMAIL_ID"],
        st.secrets["EMAIL_APP_PASSWORD"]
    )
    server.send_message(msg)
    server.quit()

# ----------------- UI SETUP -----------------
st.set_page_config(page_title="PolicyNav", layout="centered")

# ----------------- SIDEBAR -----------------
if not st.session_state.get("logged_in"):
    choice = st.sidebar.selectbox(
        "Menu", ["Login", "Signup", "Forgot Password"]
    )
else:
    choice = None
    st.sidebar.success("Logged in")
    st.sidebar.info("🔐 OTP Authentication Enabled")
    st.sidebar.info("📊 Readability Dashboard Enabled")

# ----------------- SIGNUP -----------------
if choice == "Signup":
    st.title("📝 Signup")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    question = st.selectbox(
        "Security Question",
        ["Pet name?", "Mother's maiden name?", "Favourite teacher?"]
    )
    answer = st.text_input("Security Answer")

    if st.button("Signup"):
        if not all([username, email, password, confirm, answer]):
            st.error("All fields required")
        elif password != confirm:
            st.error("Passwords do not match")
        else:
            c.execute(
                "INSERT OR REPLACE INTO users VALUES (?,?,?,?,?)",
                (username, email, password, question, answer)
            )
            conn.commit()
            st.success("Signup successful")

# ----------------- LOGIN WITH OTP -----------------
elif choice == "Login":
    st.title("🔐 Login with OTP")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Send OTP"):
        c.execute(
            "SELECT username FROM users WHERE email=? AND password=?",
            (email, password)
        )
        user = c.fetchone()

        if user:
            otp = random.randint(100000, 999999)
            st.session_state["otp"] = str(otp)
            st.session_state["user"] = user[0]
            st.session_state["email"] = email
            send_otp(email, otp)
            st.success("OTP sent to email")
        else:
            st.error("Invalid credentials")

    if "otp" in st.session_state:
        entered = st.text_input("Enter OTP")
        if st.button("Verify OTP"):
            if entered == st.session_state["otp"]:
                st.session_state["logged_in"] = True
                st.success("Login successful")
                st.rerun()   # ✅ FIX
            else:
                st.error("Wrong OTP")

# ----------------- FORGOT PASSWORD -----------------
elif choice == "Forgot Password":
    st.title("🔁 Forgot Password")
    email = st.text_input("Email")

    if st.button("Get Question"):
        c.execute("SELECT question, answer FROM users WHERE email=?", (email,))
        data = c.fetchone()
        if data:
            st.session_state["q"] = data[0]
            st.session_state["a"] = data[1]
            st.session_state["email"] = email
        else:
            st.error("Email not found")

    if "q" in st.session_state:
        st.write("Question:", st.session_state["q"])
        ans = st.text_input("Your Answer")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Reset Password"):
            if ans == st.session_state["a"]:
                c.execute(
                    "UPDATE users SET password=? WHERE email=?",
                    (new_pass, st.session_state["email"])
                )
                conn.commit()
                st.success("Password updated")
            else:
                st.error("Wrong answer")

# ----------------- DASHBOARD -----------------
if st.session_state.get("logged_in"):
    st.title("🏠 PolicyNav Dashboard")
    st.write(f"Welcome **{st.session_state['user']}** 👋")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()   # ✅ FIX

    st.divider()
    st.subheader("📊 Readability Dashboard")

    text = st.text_area(
        "Paste policy text here",
        "Public policy aims to improve citizen welfare."
    )

    wc = len(text.split())
    sc = text.count(".") + 1

    c1, c2 = st.columns(2)
    c1.metric("Word Count", wc)
    c2.metric("Sentence Count", sc)

    if wc < 20:
        st.success("Easy to read 👍")
    elif wc < 40:
        st.warning("Moderate readability ⚠️")
    else:
        st.error("Complex text ❌")
