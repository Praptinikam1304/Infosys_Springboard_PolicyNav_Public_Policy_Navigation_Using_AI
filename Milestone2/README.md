# 🛡️ PolicyNav - Milestone 2

## Advanced Authentication + Readability Dashboard

A Streamlit web application built for the **Infosys Springboard Internship - Milestone 2**.

---

## ✨ Features

### 🔐 Authentication
- **Signup** — Full name, email, password (with constraints), security Q&A
- **User Login** — Email + Password → OTP via Email → Dashboard
- **Admin Login** — Email + Password → Direct Dashboard (no OTP)
- **Forgot Password** — Email → Security Question → OTP → New Password (cannot reuse old password)

### 📖 User Dashboard - Readability Analyzer
- Paste text **or** upload file (`.txt`, `.pdf`, `.docx`)
- **Overall Level** banner (Elementary / High School / College / Professional)
- **Gauge Charts** — Flesch, FK Grade, SMOG, Gunning Fog, Coleman-Liau, Dale-Chall, ARI, Linsear
- **Text Statistics** — Words, Sentences, Syllables, Complex Words, Characters
- **Radar/Spider Chart** — Visual complexity overview
- **Word Cloud** — Most frequent words

### 🔐 Admin Dashboard
- Total users count
- All registered users table (Name, Email, Registered On)
- Registration Timeline chart
- Remove user option

---

## 🔑 Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*...)

---

## 🚀 How to Run

### Step 1: Set Colab Secrets
Go to 🔑 Secrets tab in Google Colab and add:

| Secret Name | Description |
|---|---|
| `JWT_SECRET_KEY` | Any random string e.g. `mySecret@123` |
| `NGROK_AUTHTOKEN` | From [ngrok.com](https://ngrok.com) |
| `EMAIL_ID` | Your Gmail address |
| `EMAIL_APP_PASSWORD` | Gmail App Password (16 chars) |
| `ADMIN_EMAIL_ID` | Admin login email |
| `ADMIN_PASSWORD` | Admin login password |

### Step 2: Run the Notebook
1. Open `PolicyNav_Milestone2_v5.ipynb` in Google Colab
2. Set all 6 secrets in the 🔑 Secrets tab
3. Click **Runtime → Run All**
4. Click the ngrok URL that appears in the last cell

---

## 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| Python | Backend logic |
| Streamlit | Web UI framework |
| SQLite | User database |
| JWT | Token-based auth |
| SMTP / Gmail | OTP email sending |
| Textstat | Readability scoring |
| Plotly | Gauge + Radar charts |
| WordCloud | Word frequency visualization |
| Matplotlib | Additional charts |
| Ngrok | Public URL tunneling |
| Google Colab Secrets | Secure key management |

---

## 📁 Project Structure
```
Milestone2/
├── PolicyNav_Milestone2_v5.ipynb   ← Main Colab notebook
├── app.py                           ← Streamlit app source code
├── README.md                        ← This file
└── screenshots/                     ← App screenshots
    ├── signup.png
    ├── login.png
    ├── otp.png
    ├── readability_dashboard.png
    ├── gauge_charts.png
    ├── word_cloud.png
    ├── admin_dashboard.png
    └── forgot_password.png
```

---

## 📸 Screenshots

### Signup Page
![Signup](screenshots/signup.png)

### Login Page
![Login](screenshots/login.png)

### OTP Verification
![OTP](screenshots/otp.png)

### Readability Dashboard
![Readability](screenshots/readability_dashboard.png)

### Gauge Charts
![Gauges](screenshots/gauge_charts.png)

### Admin Dashboard
![Admin](screenshots/admin_dashboard.png)

---

## 👨‍💻 Developed By
Prapti Nikam
Infosys Springboard Internship Intern— Milestone 2
