import streamlit as st
import sqlite3
import jwt
import datetime
import smtplib
import random
import string
import re
import os
import io
import textstat
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from wordcloud import WordCloud
    WORDCLOUD_OK = True
except ImportError:
    WORDCLOUD_OK = False

try:
    import docx
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    import PyPDF2
    PDF_OK = True
except ImportError:
    PDF_OK = False

# ── Secrets via Environment Variables (set by launch cell) ────────────────────
SECRET_KEY     = os.environ.get('JWT_SECRET_KEY', 'default_secret')
EMAIL_ID       = os.environ.get('EMAIL_ID', '')
EMAIL_PASS     = os.environ.get('EMAIL_APP_PASSWORD', '')
ADMIN_EMAIL    = os.environ.get('ADMIN_EMAIL_ID', 'admin@policynav.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@123')

# ── Database ───────────────────────────────────────────────────────────────────
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT,
    email    TEXT PRIMARY KEY,
    password TEXT,
    question TEXT,
    answer   TEXT,
    created  TEXT
)
""")
conn.commit()

# ── Helper Functions ───────────────────────────────────────────────────────────
def send_otp_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From']    = EMAIL_ID
        msg['To']      = to_email
        msg['Subject'] = 'PolicyNav - Your OTP Code'
        body = f"""<html><body>
        <h2 style="color:#2E86AB;">PolicyNav Authentication</h2>
        <p>Your One-Time Password (OTP) is:</p>
        <h1 style="letter-spacing:10px;color:#E84855;font-size:40px;">{otp}</h1>
        <p>This OTP is valid for <b>5 minutes</b>.</p>
        <hr/>
        <small>If you did not request this, please ignore this email.</small>
        </body></html>"""
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ID, EMAIL_PASS)
        server.sendmail(EMAIL_ID, to_email, msg.as_string())
        server.quit()
        return True, 'OTP sent successfully!'
    except Exception as e:
        return False, str(e)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def validate_password(pwd):
    errors = []
    if len(pwd) < 8:
        errors.append('At least 8 characters required')
    if not re.search(r'[A-Z]', pwd):
        errors.append('At least one uppercase letter required')
    if not re.search(r'[a-z]', pwd):
        errors.append('At least one lowercase letter required')
    if not re.search(r'\d', pwd):
        errors.append('At least one digit required')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd):
        errors.append('At least one special character required (!@#$%^&*...)')
    return errors

def make_jwt(email):
    return jwt.encode(
        {'user': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)},
        SECRET_KEY, algorithm='HS256'
    )

def extract_text_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith('.txt'):
        return uploaded_file.read().decode('utf-8', errors='ignore')
    elif name.endswith('.pdf') and PDF_OK:
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        return ' '.join(p.extract_text() or '' for p in reader.pages)
    elif name.endswith('.docx') and DOCX_OK:
        document = docx.Document(io.BytesIO(uploaded_file.read()))
        return ' '.join(p.text for p in document.paragraphs)
    return None

def compute_readability(text):
    return {
        'Flesch Reading Ease':   round(textstat.flesch_reading_ease(text), 2),
        'Flesch-Kincaid Grade':  round(textstat.flesch_kincaid_grade(text), 2),
        'Gunning Fog Index':     round(textstat.gunning_fog(text), 2),
        'SMOG Index':            round(textstat.smog_index(text), 2),
        'Coleman-Liau Index':    round(textstat.coleman_liau_index(text), 2),
        'Automated Readability': round(textstat.automated_readability_index(text), 2),
        'Dale-Chall Score':      round(textstat.dale_chall_readability_score(text), 2),
        'Linsear Write':         round(textstat.linsear_write_formula(text), 2),
    }

def ease_label(score):
    if score >= 90: return 'Very Easy', '#27ae60'
    if score >= 70: return 'Easy', '#2ecc71'
    if score >= 60: return 'Standard', '#f39c12'
    if score >= 50: return 'Fairly Difficult', '#e67e22'
    if score >= 30: return 'Difficult', '#e74c3c'
    return 'Very Difficult', '#c0392b'

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title='PolicyNav', page_icon='🛡️', layout='wide')

st.markdown("""
<style>
.block-container { padding-top: 2rem; }
.stButton>button {
    background: linear-gradient(135deg, #2E86AB, #1a5276);
    color: white; border-radius: 8px; border: none;
    padding: 0.5rem 1.5rem; font-weight: 600; width: 100%;
    transition: opacity 0.2s;
}
.stButton>button:hover { opacity: 0.85; }
.metric-card {
    background: white; border-radius: 12px; padding: 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 0.5rem;
    border-left: 4px solid #2E86AB;
}
.otp-box {
    background: #eaf4fb; border: 2px dashed #2E86AB;
    border-radius: 12px; padding: 1.5rem; text-align: center;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<h2 style="text-align:center;color:#2E86AB;">🛡️ PolicyNav</h2>', unsafe_allow_html=True)
    st.markdown('---')
    if not st.session_state.get('logged_in'):
        choice = st.radio('Navigate', ['🔑 Login', '📝 Signup', '🔒 Forgot Password'],
                          label_visibility='collapsed')
    else:
        role = st.session_state.get('role', 'user')
        choice = '📊 Admin Dashboard' if role == 'admin' else '📖 Readability Dashboard'
        st.markdown(f"**Page:** {choice}")
        st.markdown('---')
        st.markdown(f"👤 **{st.session_state.get('user_name', '')}**")
        st.markdown(f"🏷️ Role: `{role}`")
        if st.button('🚪 Logout'):
            keys_to_clear = [
                'logged_in','user_name','role',
                'otp_pending','otp_value','otp_time','otp_email','otp_name','otp_role',
                'fp_q','fp_a','fp_email','fp_otp','fp_otp_time','fp_otp_verified',
                'analysis_text'
            ]
            for k in keys_to_clear:
                st.session_state.pop(k, None)
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# SIGNUP
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.get('logged_in') and '📝 Signup' in choice:
    st.title('📝 Create Your Account')
    st.markdown('---')
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('#### Personal Details')
        username = st.text_input('👤 Full Name')
        email    = st.text_input('📧 Email Address')
        password = st.text_input('🔑 Password', type='password')
        confirm  = st.text_input('🔑 Confirm Password', type='password')

    with col2:
        st.markdown('#### Security')
        question = st.selectbox('❓ Security Question', [
            "What is your pet's name?",
            "What is your mother's maiden name?",
            "Who was your favourite teacher?",
            "What was your first school's name?",
            "What is your childhood nickname?"
        ])
        answer = st.text_input('💬 Security Answer')
        st.markdown('**Password Requirements:**')
        st.info('✔ Minimum 8 characters\n✔ Uppercase & lowercase letters\n✔ At least 1 digit\n✔ At least 1 special character')

    if password:
        errs = validate_password(password)
        if errs:
            for e in errs:
                st.warning(f'⚠ {e}')
        else:
            st.success('✅ Password strength: Strong')

    st.markdown('---')
    if st.button('Create Account ✨'):
        if not all([username, email, password, confirm, answer]):
            st.error('❌ All fields are required.')
        elif not re.match(r'^[\w.+-]+@[\w-]+\.[\w.]+$', email):
            st.error('❌ Invalid email format.')
        elif password != confirm:
            st.error('❌ Passwords do not match.')
        elif validate_password(password):
            st.error('❌ Password does not meet the requirements.')
        else:
            c.execute('SELECT email FROM users WHERE email=?', (email,))
            if c.fetchone():
                st.error('❌ This email is already registered. Please login.')
            else:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute('INSERT INTO users VALUES (?,?,?,?,?,?)',
                          (username, email, password, question, answer.lower().strip(), now))
                conn.commit()
                st.success('🎉 Account created successfully! Please login.')
                st.balloons()

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
elif not st.session_state.get('logged_in') and '🔑 Login' in choice:
    st.title('🔑 Login to PolicyNav')
    st.markdown('---')

    login_type = st.radio('Login As', ['👤 User', '🔐 Admin'], horizontal=True)
    st.markdown('---')
    email    = st.text_input('📧 Email Address')
    password = st.text_input('🔒 Password', type='password')
    st.markdown('')

    # ── ADMIN LOGIN (no OTP) ──────────────────────────────────────────────────
    if '🔐 Admin' in login_type:
        if st.button('Login →', use_container_width=True):
            if not email or not password:
                st.error('❌ Please enter email and password.')
            elif email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                st.session_state.update({
                    'logged_in': True,
                    'user_name': 'Admin',
                    'role':      'admin'
                })
                st.success('✅ Admin login successful!')
                st.rerun()
            else:
                st.error('❌ Invalid admin credentials.')

    # ── USER LOGIN (with OTP) ─────────────────────────────────────────────────
    else:
        if not st.session_state.get('otp_pending'):
            if st.button('Get OTP →', use_container_width=True):
                if not email or not password:
                    st.error('❌ Please enter email and password.')
                else:
                    c.execute('SELECT username FROM users WHERE email=? AND password=?', (email, password))
                    row = c.fetchone()
                    if row:
                        otp = generate_otp()
                        ok, msg = send_otp_email(email, otp)
                        st.session_state.update({
                            'otp_pending': True,
                            'otp_value':   otp,
                            'otp_time':    datetime.datetime.now(),
                            'otp_email':   email,
                            'otp_name':    row[0],
                            'otp_role':    'user'
                        })
                        if ok:
                            st.success(f'📨 OTP sent to {email}! Check your inbox.')
                        else:
                            st.warning(f'⚠ Could not send email ({msg}).\n\n**Demo Mode — OTP: `{otp}`**')
                        st.rerun()
                    else:
                        st.error('❌ Invalid credentials. Please check email and password.')

        else:
            st.markdown(f'<div class="otp-box">📨 OTP sent to <b>{st.session_state["otp_email"]}</b><br/>Check your inbox (or see warning above in Demo Mode)</div>',
                        unsafe_allow_html=True)
            otp_input = st.text_input('🔢 Enter 6-digit OTP', max_chars=6, placeholder='e.g. 482910')
            st.markdown('')
            col1, col2 = st.columns(2)
            with col1:
                if st.button('✅ Verify OTP', use_container_width=True):
                    elapsed = (datetime.datetime.now() - st.session_state['otp_time']).seconds
                    if elapsed > 300:
                        st.error('⏰ OTP has expired. Please login again.')
                        st.session_state.pop('otp_pending', None)
                        st.rerun()
                    elif otp_input == st.session_state['otp_value']:
                        st.session_state.update({
                            'logged_in': True,
                            'user_name': st.session_state['otp_name'],
                            'role':      st.session_state['otp_role']
                        })
                        for k in ['otp_pending','otp_value','otp_time','otp_email','otp_name','otp_role']:
                            st.session_state.pop(k, None)
                        st.success('🎉 Login successful!')
                        st.rerun()
                    else:
                        st.error('❌ Incorrect OTP. Please try again.')
            with col2:
                if st.button('↩ Back to Login', use_container_width=True):
                    for k in ['otp_pending','otp_value','otp_time','otp_email','otp_name','otp_role']:
                        st.session_state.pop(k, None)
                    st.rerun()
# ═══════════════════════════════════════════════════════════════════════════════
# FORGOT PASSWORD
# ═══════════════════════════════════════════════════════════════════════════════
elif not st.session_state.get('logged_in') and '🔒 Forgot Password' in choice:
    st.title('🔒 Reset Your Password')
    st.markdown('---')

    # Progress indicator
    if not st.session_state.get('fp_q'):
        step = 1
    elif not st.session_state.get('fp_otp_verified'):
        step = 2
    else:
        step = 3
    st.markdown(f'**Step {step} of 3** — {"Enter Email" if step==1 else "Verify Identity" if step==2 else "Set New Password"}')
    st.progress(step / 3)
    st.markdown('---')

    # Step 1: Email
    if step == 1:
        email = st.text_input('📧 Enter your registered email')
        if st.button('Continue →'):
            if not email:
                st.error('❌ Please enter your email.')
            else:
                c.execute('SELECT question, answer FROM users WHERE email=?', (email,))
                row = c.fetchone()
                if row:
                    st.session_state.update({'fp_q': row[0], 'fp_a': row[1], 'fp_email': email})
                    st.rerun()
                else:
                    st.error('❌ Email not found. Please check and try again.')

    # Step 2: Security Question + OTP
    elif step == 2:
        st.info(f'🔐 **Security Question:** {st.session_state["fp_q"]}')
        ans = st.text_input('💬 Your Answer')
        st.markdown('')
        if st.button('Send OTP 📨'):
            if not ans:
                st.error('❌ Please enter your answer.')
            elif ans.lower().strip() == st.session_state['fp_a']:
                otp = generate_otp()
                ok, msg = send_otp_email(st.session_state['fp_email'], otp)
                st.session_state.update({'fp_otp': otp, 'fp_otp_time': datetime.datetime.now()})
                if ok:
                    st.success('📨 OTP sent to your email!')
                else:
                    st.warning(f'Demo Mode — OTP: **{otp}** ({msg})')
            else:
                st.error('❌ Wrong answer. Please try again.')

        if st.session_state.get('fp_otp'):
            st.markdown('---')
            otp_in = st.text_input('🔢 Enter OTP', max_chars=6, placeholder='6-digit OTP')
            col1, col2 = st.columns(2)
            with col1:
                if st.button('✅ Verify OTP'):
                    elapsed = (datetime.datetime.now() - st.session_state['fp_otp_time']).seconds
                    if elapsed > 300:
                        st.error('⏰ OTP expired. Please try again.')
                        st.session_state.pop('fp_otp', None)
                    elif otp_in == st.session_state['fp_otp']:
                        st.session_state['fp_otp_verified'] = True
                        st.rerun()
                    else:
                        st.error('❌ Incorrect OTP.')
            with col2:
                if st.button('↩ Start Over'):
                    for k in ['fp_q','fp_a','fp_email','fp_otp','fp_otp_time','fp_otp_verified']:
                        st.session_state.pop(k, None)
                    st.rerun()

    # Step 3: New Password
    else:
        st.success('✅ Identity verified! Set your new password below.')
        st.markdown('---')
        new_pass  = st.text_input('🔑 New Password', type='password')
        conf_pass = st.text_input('🔑 Confirm New Password', type='password')

        if new_pass:
            errs = validate_password(new_pass)
            if errs:
                for e in errs:
                    st.warning(f'⚠ {e}')
            else:
                st.success('✅ Password strength: Strong')

        st.markdown('')
        if st.button('Reset Password 🔄'):
            c.execute('SELECT password FROM users WHERE email=?', (st.session_state['fp_email'],))
            old = c.fetchone()
            if not new_pass or not conf_pass:
                st.error('❌ Please fill both fields.')
            elif old and new_pass == old[0]:
                st.error('❌ New password cannot be same as your old password.')
            elif new_pass != conf_pass:
                st.error('❌ Passwords do not match.')
            elif validate_password(new_pass):
                st.error('❌ Password does not meet the requirements.')
            else:
                c.execute('UPDATE users SET password=? WHERE email=?',
                          (new_pass, st.session_state['fp_email']))
                conn.commit()
                for k in ['fp_q','fp_a','fp_email','fp_otp','fp_otp_time','fp_otp_verified']:
                    st.session_state.pop(k, None)
                st.success('🎉 Password reset successfully! Please login.')
                st.balloons()

# ═══════════════════════════════════════════════════════════════════════════════
# USER - READABILITY DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.get('logged_in') and st.session_state.get('role') == 'user':
    import numpy as np
    import plotly.graph_objects as go

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:2rem;border-radius:16px;margin-bottom:1rem;">
        <h1 style="color:white;margin:0;">📖 Readability Dashboard</h1>
        <p style="color:#aaa;margin:0.5rem 0 0 0;">Welcome back, <b style="color:#00d4aa">{st.session_state['user_name']}</b> 👋</p>
    </div>
    """, unsafe_allow_html=True)

    input_method = st.radio('Input Method', ['📝 Paste Text', '📁 Upload File'], horizontal=True)
    text = ''

    if '📝 Paste Text' in input_method:
        text = st.text_area('Paste your policy/document text here:',
                            height=220,
                            placeholder='Paste any policy, insurance document, legal text, or article here...')
    else:
        up = st.file_uploader('Upload a file (.txt, .pdf, .docx)', type=['txt','pdf','docx'])
        if up:
            with st.spinner('Extracting text from file...'):
                text = extract_text_from_file(up)
            if text:
                st.success(f'✅ Text extracted successfully! ({len(text.split())} words found)')
                with st.expander('📄 Extracted Text Preview'):
                    st.write(text[:3000] + ('...' if len(text) > 3000 else ''))
            else:
                st.error('Could not extract text. Ensure file is not empty or encrypted.')

    if text:
        word_count = len(text.split())
        st.caption(f'Word count: {word_count}')
        if word_count >= 10:
            if st.button('🔍 Analyze Readability', use_container_width=True):
                st.session_state['analysis_text'] = text
        else:
            st.warning('⚠ Please enter at least 10 words for analysis.')

    if st.session_state.get('analysis_text'):
        text   = st.session_state['analysis_text']
        scores = compute_readability(text)
        ease   = scores['Flesch Reading Ease']
        fk     = scores['Flesch-Kincaid Grade']
        smog   = scores['SMOG Index']
        fog    = scores['Gunning Fog Index']
        cl     = scores['Coleman-Liau Index']
        dc     = scores['Dale-Chall Score']
        ari    = scores['Automated Readability']
        lw     = scores['Linsear Write']

        # Overall level
        grade = round((fk + smog + fog + cl) / 4, 1)
        if grade <= 6:   overall, badge_color = 'Elementary', '#27ae60'
        elif grade <= 8: overall, badge_color = 'Middle School', '#2ecc71'
        elif grade <= 10: overall, badge_color = 'High School', '#f39c12'
        elif grade <= 12: overall, badge_color = 'Advanced (High School/College)', '#e67e22'
        else:            overall, badge_color = 'Professional/Expert', '#e74c3c'

        label, ease_color = ease_label(ease)

        # ── Overall banner ──────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#1a1a2e;border:2px solid {badge_color};border-radius:12px;
                    padding:1.5rem;text-align:center;margin:1rem 0;">
            <h2 style="color:white;margin:0;">Overall Level: {overall}</h2>
            <p style="color:#aaa;margin:0.5rem 0 0 0;">Approximate Grade Level: {grade}</p>
        </div>
        """, unsafe_allow_html=True)

        # ── Text Statistics ──────────────────────────────────────────────────
        st.markdown('### 📝 Text Statistics')
        words     = textstat.lexicon_count(text)
        sentences = textstat.sentence_count(text)
        syllables = textstat.syllable_count(text)
        chars     = len(text)
        complex_w = textstat.difficult_words(text)

        c1,c2,c3,c4,c5 = st.columns(5)
        for col, label_s, val in [
            (c1,'Sentences', sentences),
            (c2,'Words', words),
            (c3,'Syllables', syllables),
            (c4,'Complex Words', complex_w),
            (c5,'Characters', chars)
        ]:
            col.markdown(f"""
            <div style="background:#1a1a2e;border-radius:10px;padding:1rem;text-align:center;border:1px solid #333;">
                <p style="color:#aaa;margin:0;font-size:0.8rem;">{label_s}</p>
                <h3 style="color:white;margin:0.3rem 0 0 0;">{val:,}</h3>
            </div>""", unsafe_allow_html=True)

        # ── Gauge Charts ──────────────────────────────────────────────────────
        st.markdown('### 📊 Detailed Metrics')

        def make_gauge(value, title, min_val, max_val, color):
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                title={'text': title, 'font': {'color': 'white', 'size': 14}},
                number={'font': {'color': 'white', 'size': 36}},
                gauge={
                    'axis': {'range': [min_val, max_val],
                             'tickcolor': 'gray',
                             'tickfont': {'color': 'gray'}},
                    'bar': {'color': color, 'thickness': 0.3},
                    'bgcolor': '#1a1a2e',
                    'bordercolor': '#333',
                    'steps': [
                        {'range': [min_val, max_val*0.33], 'color': '#0d1117'},
                        {'range': [max_val*0.33, max_val*0.66], 'color': '#111827'},
                        {'range': [max_val*0.66, max_val], 'color': '#1a1a2e'}
                    ],
                }
            ))
            fig.update_layout(
                paper_bgcolor='#0d1117',
                plot_bgcolor='#0d1117',
                font={'color': 'white'},
                height=220,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return fig

        # Row 1: 3 gauges
        g1, g2, g3 = st.columns(3)
        with g1:
            st.plotly_chart(make_gauge(ease, 'Flesch Reading Ease', 0, 100, '#00d4aa'), use_container_width=True)
        with g2:
            st.plotly_chart(make_gauge(fk, 'Flesch-Kincaid Grade', 0, 20, '#ff00ff'), use_container_width=True)
        with g3:
            st.plotly_chart(make_gauge(smog, 'SMOG Index', 0, 20, '#ffff00'), use_container_width=True)

        # Row 2: 2 gauges
        g4, g5 = st.columns(2)
        with g4:
            st.plotly_chart(make_gauge(fog, 'Gunning Fog Index', 0, 20, '#00bfff'), use_container_width=True)
        with g5:
            st.plotly_chart(make_gauge(cl, 'Coleman-Liau Index', 0, 20, '#ff8c00'), use_container_width=True)

        # Row 3: 3 gauges
        g6, g7, g8 = st.columns(3)
        with g6:
            st.plotly_chart(make_gauge(dc, 'Dale-Chall Score', 0, 15, '#ff4444'), use_container_width=True)
        with g7:
            st.plotly_chart(make_gauge(ari, 'Automated Readability', 0, 20, '#9b59b6'), use_container_width=True)
        with g8:
            st.plotly_chart(make_gauge(lw, 'Linsear Write', 0, 20, '#1abc9c'), use_container_width=True)

        # ── Radar Chart ──────────────────────────────────────────────────────
        st.markdown('### 🕸 Radar Overview')
        radar_labels = ['Flesch Ease', 'FK Grade (inv)', 'Gunning Fog (inv)',
                        'Coleman (inv)', 'Dale-Chall (inv)', 'SMOG (inv)']
        radar_vals = [
            min(max(ease, 0), 100),
            max(0, 100 - fk * 5),
            max(0, 100 - fog * 4),
            max(0, 100 - cl * 5),
            max(0, 100 - dc * 10),
            max(0, 100 - smog * 4),
        ]
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(
            r=radar_vals + [radar_vals[0]],
            theta=radar_labels + [radar_labels[0]],
            fill='toself',
            fillcolor='rgba(0,212,170,0.2)',
            line=dict(color='#00d4aa', width=2),
            marker=dict(color='#00d4aa', size=8),
            name='Readability'
        ))
        fig_r.update_layout(
            polar=dict(
                bgcolor='#1a1a2e',
                radialaxis=dict(visible=True, range=[0,100], color='gray', gridcolor='#333'),
                angularaxis=dict(color='white', gridcolor='#333')
            ),
            paper_bgcolor='#0d1117',
            plot_bgcolor='#0d1117',
            font=dict(color='white'),
            showlegend=False,
            height=420,
            title=dict(text='Readability Spider Chart (higher = easier to read)',
                      font=dict(color='white', size=14), x=0.5)
        )
        st.plotly_chart(fig_r, use_container_width=True)

        # ── Word Cloud ────────────────────────────────────────────────────────
        st.markdown('### ☁ Word Cloud')
        if WORDCLOUD_OK:
            wc = WordCloud(width=1000, height=400, background_color='#0d1117',
                           colormap='cool', max_words=150,
                           contour_color='#00d4aa', contour_width=1).generate(text)
            fig_wc, ax_wc = plt.subplots(figsize=(12, 4), facecolor='#0d1117')
            ax_wc.imshow(wc, interpolation='bilinear')
            ax_wc.axis('off')
            plt.tight_layout(pad=0)
            st.pyplot(fig_wc)
            plt.close()
        else:
            words_list = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            freq = {}
            for w in words_list:
                freq[w] = freq.get(w, 0) + 1
            top = sorted(freq.items(), key=lambda x: -x[1])[:25]
            if top:
                fig_wc2 = go.Figure(go.Bar(
                    x=[x[0] for x in top], y=[x[1] for x in top],
                    marker_color=['#00d4aa','#ff00ff','#ffff00','#00bfff','#ff8c00'] * 5,
                    text=[x[1] for x in top], textposition='outside',
                    textfont=dict(color='white')
                ))
                fig_wc2.update_layout(
                    paper_bgcolor='#0d1117', plot_bgcolor='#0d1117',
                    font=dict(color='white'),
                    title='Top 25 Most Frequent Words',
                    xaxis=dict(tickangle=45, gridcolor='#333'),
                    yaxis=dict(gridcolor='#333'),
                    height=400
                )
                st.plotly_chart(fig_wc2, use_container_width=True)

        # ── Interpretation ────────────────────────────────────────────────────
        with st.expander('ℹ️ How to interpret Flesch Reading Ease score?'):
            st.markdown("""
            | Score | Level | Audience |
            |---|---|---|
            | 90 - 100 | Very Easy | 5th Grade |
            | 70 - 90 | Easy | 6th Grade |
            | 60 - 70 | Standard | 7th Grade |
            | 50 - 60 | Fairly Difficult | 8th-9th Grade |
            | 30 - 50 | Difficult | College |
            | 0 - 30 | Very Difficult | Professional |
            """)

        if st.button('🗑 Clear Analysis'):
            st.session_state.pop('analysis_text', None)
            st.rerun()
    elif text and len(text.split()) < 10:
        st.warning('Please enter at least 10 words.')
# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.get('logged_in') and st.session_state.get('role') == 'admin':
    st.title('🔐 Admin Dashboard')
    st.markdown('---')

    c.execute('SELECT username, email, created FROM users')
    rows = c.fetchall()

    col1, col2, col3 = st.columns(3)
    col1.metric('👥 Total Users', len(rows))
    today     = datetime.date.today().strftime('%Y-%m-%d')
    new_today = sum(1 for r in rows if r[2] and r[2].startswith(today))
    col2.metric('🆕 Registered Today', new_today)
    col3.metric('📧 Admin Email', ADMIN_EMAIL)

    st.markdown('---')
    st.markdown('### 👥 All Registered Users')

    if rows:
        import pandas as pd
        df = pd.DataFrame(rows, columns=['Name', 'Email', 'Registered On'])
        df.index = df.index + 1
        st.dataframe(df, use_container_width=True)

        st.markdown('### 📈 Registration Timeline')
        df['Date'] = pd.to_datetime(df['Registered On'], errors='coerce').dt.date
        daily = df.groupby('Date').size().reset_index(name='Count')
        fig, ax = plt.subplots(figsize=(10, 4))
        date_labels = [str(d) for d in daily['Date']]
        ax.plot(date_labels, daily['Count'].values, marker='o',
                color='#2E86AB', linewidth=2, markersize=8)
        ax.fill_between(range(len(daily)), daily['Count'].values, alpha=0.2, color='#2E86AB')
        ax.set_title('Daily User Registrations', fontweight='bold', fontsize=14)
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Users')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.markdown('### 🗑 Remove a User')
        email_list = [r[1] for r in rows]
        del_email  = st.selectbox('Select user to remove', ['-- select --'] + email_list)
        if del_email != '-- select --':
            st.warning(f'You are about to remove **{del_email}**. This cannot be undone.')
            if st.button(f'❌ Confirm Remove {del_email}'):
                c.execute('DELETE FROM users WHERE email=?', (del_email,))
                conn.commit()
                st.success(f'✅ User {del_email} has been removed.')
                st.rerun()
    else:
        st.info('No users registered yet.')
