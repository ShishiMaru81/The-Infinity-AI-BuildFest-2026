# GuardianAI — Testing Setup Guide

**Document version:** 1.0  
**Purpose:** Everything you need to manage for **test/demo mode only** (no real 999 dispatch).

---

## Legal notice (testing)

- Keep **Demo / Test Mode** ON during development and competition demos.
- In test mode, emails go to **your test inbox**, not `999@police.gov.bd`.
- False reports to Bangladesh National Emergency Service (999) may be a **criminal offense**.

---

## 1. What you must manage (required)

| # | Item | What to do |
|---|------|------------|
| 1 | **`backend/.env`** | Copy from `.env.example`: `copy .env.example .env` — put real secrets here only |
| 2 | **`APP_MODE=test`** | In `.env` — never use `real` for classroom testing |
| 3 | **`TEST_EMAIL`** | Your real inbox (e.g. `you@gmail.com`) — you verify alerts arrived |
| 4 | **SMTP settings** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SENDER_EMAIL` |
| 5 | **`frontend/.env.local`** | Copy from `.env.local.example` — keep API URLs on localhost |
| 6 | **Backend server** | Run `start-backend.ps1` → http://127.0.0.1:8000 |
| 7 | **Frontend server** | Run `start-frontend.ps1` → http://localhost:3000 |
| 8 | **Webcam** | Allow camera permission in Chrome/Edge |
| 9 | **UI mode** | Dashboard header must show **Demo / Test Mode** (green) |

### Frontend `.env.local` (default)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/live
```

---

## 2. What you should set (recommended)

| # | Variable | Suggested for testing |
|---|----------|------------------------|
| 10 | `REPORTER_NAME` | Your name (appears in email) |
| 11 | `REPORTER_PHONE` | Your phone, e.g. `+88017XXXXXXXX` |
| 12 | `FALLBACK_ADDRESS` | e.g. `Mirpur, Dhaka, Bangladesh` |
| 13 | `DETECTION_CONFIDENCE_THRESHOLD` | `0.6` (lower = more sensitive) |
| 14 | `DETECTION_CONSECUTIVE_FRAMES` | `5` (use `3` for faster demo trigger) |
| 15 | `FRAME_FPS` | `8` (lower if laptop is slow) |
| 16 | `ALERT_MODE` | `mock` (Twilio only logs, no real calls) |
| 17 | **Test prop** | Knife or clear photo — default model detects **knife** best |

---

## 3. What you do NOT need for testing (leave empty)

| Variable | In test mode |
|----------|----------------|
| `TWILIO_ACCOUNT_SID` | Skipped |
| `TWILIO_AUTH_TOKEN` | Skipped |
| `TWILIO_PHONE_NUMBER` | Skipped |
| `ANTHROPIC_API_KEY` | Optional (plain email works without it) |
| `ROBOFLOW_API_KEY` | Optional (only for gun/fire/lighter) |
| `ROBOFLOW_WEAPON_MODEL` | Optional |
| `ROBOFLOW_FIRE_MODEL` | Optional |
| **Real Mode** in UI | Keep OFF |

---

## 4. Minimal `backend/.env` template (testing)

```env
APP_MODE=test
TEST_EMAIL=your.real.email@gmail.com
EMERGENCY_EMAIL=999@police.gov.bd
REAL_DISPATCH_COOLDOWN_SEC=300

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.real.email@gmail.com
SMTP_PASS=your_gmail_app_password
SENDER_EMAIL=your.real.email@gmail.com

REPORTER_NAME=Your Name
REPORTER_PHONE=+88017XXXXXXXX
FALLBACK_ADDRESS=Mirpur, Dhaka, Bangladesh

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
POLICE_NUMBER=999
TEST_PHONE=
ALERT_MODE=mock

FRAME_FPS=8
YOLO_MODEL=yolov8n.pt
DETECTION_CONFIDENCE_THRESHOLD=0.6
DETECTION_CONSECUTIVE_FRAMES=5

ROBOFLOW_API_KEY=
ROBOFLOW_WEAPON_MODEL=
ROBOFLOW_FIRE_MODEL=

DATABASE_URL=sqlite+aiosqlite:///./guardianai.db
DEFAULT_LAT=23.8103
DEFAULT_LNG=90.4125
```

---

## 5. Gmail SMTP setup (step by step)

1. Open Google Account → **Security**.
2. Enable **2-Step Verification**.
3. Create an **App password** (Mail).
4. Copy the 16-character password into `SMTP_PASS` (spaces are OK).
5. Set `SMTP_USER` and `SENDER_EMAIL` to your Gmail address.

**Do not** use your normal Gmail login password in `SMTP_PASS`.

---

## 6. How to start the app

Open **two** PowerShell terminals in the project folder:

**Terminal 1 — Backend**

```powershell
.\start-backend.ps1
```

Wait for: `Starting GuardianAI API at http://127.0.0.1:8000`

**Terminal 2 — Frontend**

```powershell
.\start-frontend.ps1
```

Wait for: `http://localhost:3000`

**Restart backend** after any change to `backend/.env`.

---

## 7. Five-minute test procedure

| Step | Action | Expected result |
|------|--------|-----------------|
| 1 | Open http://localhost:3000 | Dashboard loads |
| 2 | Confirm header: **Demo / Test Mode** | Green badge |
| 3 | Click **Start Webcam** | Live video appears |
| 4 | Show a **knife** (or clear image) for ~5 seconds | Bounding boxes + confidence bar |
| 5 | Hazard modal opens | Snapshot, countdown, two buttons |
| 6 | Click **Confirm & Dispatch** (or wait 10s) | Status: email sent / skipped |
| 7 | Check **TEST_EMAIL** inbox | URGENT alert email with attachment |
| 8 | Open `backend/dispatch_log.json` | `"mode": "test"` |
| 9 | Click **False Alarm** (separate test) | Modal closes without dispatch |

---

## 8. Files to check after testing

| File | What to verify |
|------|----------------|
| `backend/dispatch_log.json` | `"mode": "test"`, `"email_status": "sent"` |
| Your test email inbox | Subject contains threat type (e.g. knife) |
| Backend terminal | No SMTP login errors |

---

## 9. Troubleshooting

| Problem | Fix |
|---------|-----|
| Email not received | Check SMTP app password; restart backend |
| No detection / no boxes | Better lighting; lower threshold to `0.5`; use knife prop |
| Modal never opens | Increase hold time; lower `DETECTION_CONSECUTIVE_FRAMES` to `3` |
| Frontend can't connect | Backend running? Check `.env.local` URLs |
| Email went to 999 | Set `APP_MODE=test` and UI **Demo / Test Mode** |
| Gun/fire not detected | Normal with default YOLO — add Roboflow or custom model |

---

## 10. Security checklist

- [ ] Real passwords only in `backend/.env` (never in `.env.example`)
- [ ] `.env` and `.env.local` are **not** committed to Git
- [ ] `APP_MODE=test` before every demo
- [ ] Real Mode disabled unless judges explicitly allow it

---

## 11. One-page summary

**For testing you manage:**

1. Test mode ON (`APP_MODE=test` + green UI badge)  
2. SMTP + your `TEST_EMAIL`  
3. Both servers running (backend + frontend)  
4. Webcam + knife (or test image)  
5. Detection thresholds (Settings page or `.env`)  

**You do not need:** Twilio, Roboflow, Anthropic, or Real Mode.

---

## 12. Save as PDF (optional)

1. Open this file in VS Code / Cursor or upload to Google Docs.  
2. **File → Print → Save as PDF**, or use an online Markdown-to-PDF tool.  
3. A print-friendly HTML copy is also in: `docs/GuardianAI-Testing-Setup-Guide.html`

---

*GuardianAI — CSE AI Competition / CloudCamp Bangladesh*
