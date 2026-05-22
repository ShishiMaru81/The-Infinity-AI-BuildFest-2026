# GuardianAI — The Infinity AI BuildFest 2026

**AI-powered real-time hazard detection and emergency dispatch for Bangladesh**

GuardianAI detects **knife, gun, fire, and lighter** from a live webcam, confirms threats over consecutive frames, then dispatches an AI-composed email (and optional Twilio SMS/call) to Bangladesh emergency services — with **Demo/Test Mode enabled by default**.

![GuardianAI](https://img.shields.io/badge/Next.js-14-black) ![FastAPI](https://img.shields.io/badge/FastAPI-Python-green) ![YOLOv8](https://img.shields.io/badge/Vision-YOLOv8-blue)

---

## Legal disclaimer

**Filing false reports to Bangladesh National Emergency Service (999) is a criminal offense.** This software is for authorized safety monitoring and competition demos. Always use **Demo / Test Mode** during development. You must explicitly enable **Real Mode** to contact `999@police.gov.bd`.

---

## Features

| Module | Description |
|--------|-------------|
| **Hazard detection** | YOLOv8 + optional Roboflow models → `knife`, `gun`, `fire`, `lighter` |
| **Stability** | Configurable confidence (default 0.6) + N consecutive frames (default 5) |
| **Live UI** | Bounding boxes, flashing alert border, sound, snapshot modal, 10s auto-dispatch |
| **Dispatch agent** | LLM email body, SMTP to 999 (or test inbox), Twilio SMS/call (graceful skip) |
| **Safety** | Test mode default, real-mode confirmation, 5‑minute real-dispatch cooldown |
| **Logging** | `backend/dispatch_log.json` with email/call/SMS status |

---

## Project structure

```
backend/app/
  detection/       # hazard classes, YOLO+Roboflow ensemble, frame tracker
  vision/          # pipeline fusion
  agent/           # dispatcher, LLM email composer
  integrations/    # SMTP, Twilio wrappers
  utils/           # cooldown, dispatch_log.json
  api/             # REST + WebSocket
frontend/
  app/             # dashboard + settings
  components/      # VideoFeed, AlertModal, …
  lib/             # api client, app mode (localStorage)
```

---

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 18+
- SMTP credentials (Gmail app password, SendGrid, etc.) for email dispatch
- Optional: `ANTHROPIC_API_KEY`, `ROBOFLOW_API_KEY`, Twilio credentials

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set SMTP_*, TEST_EMAIL, APP_MODE=test
python run.py
```

API: http://localhost:8000 — Docs: http://localhost:8000/docs

### Frontend

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Dashboard: http://localhost:3000

Or from project root:

```powershell
.\start-backend.ps1   # terminal 1
.\start-frontend.ps1  # terminal 2
```

---

## Environment variables

Copy `backend/.env.example` → `backend/.env`. Never commit real secrets.

| Variable | Description |
|----------|-------------|
| `APP_MODE` | `test` (default) or `real` |
| `TEST_EMAIL` | Inbox for test-mode emails |
| `EMERGENCY_EMAIL` | Real target (`999@police.gov.bd`) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SENDER_EMAIL` | Email dispatch |
| `ANTHROPIC_API_KEY` | LLM email body (+ optional vision) |
| `REPORTER_NAME`, `REPORTER_PHONE` | Included in alert emails |
| `FALLBACK_ADDRESS` | Location if browser GPS denied |
| `DETECTION_CONFIDENCE_THRESHOLD` | Default `0.6` |
| `DETECTION_CONSECUTIVE_FRAMES` | Default `5` |
| `FRAME_FPS` | Inference rate (default `8`) |
| `REAL_DISPATCH_COOLDOWN_SEC` | Default `300` |
| `ROBOFLOW_API_KEY`, `ROBOFLOW_WEAPON_MODEL`, `ROBOFLOW_FIRE_MODEL` | Optional better gun/fire/lighter |
| `YOLO_MODEL` | Path to custom fine-tuned weights |
| `TWILIO_*`, `POLICE_NUMBER` | Optional SMS/call |

---

## Test vs real mode

- **Test mode (default):** Emails go to `TEST_EMAIL`. No live Twilio call/SMS. UI shows green “Demo / Test Mode”.
- **Real mode:** Emails go to `999@police.gov.bd`. Twilio used if configured. Toggle requires confirmation dialog. Cooldown: max 1 real dispatch per 5 minutes.

Toggle from the dashboard header or **Settings** page. Frontend also stores preference in `localStorage`.

---

## Improving detection (budget-friendly)

1. **COCO YOLOv8n** detects `knife` only reliably out of the box.
2. Add **Roboflow** (free tier): set `ROBOFLOW_WEAPON_MODEL` and `ROBOFLOW_FIRE_MODEL` to `workspace/project/version` slugs from [Roboflow Universe](https://universe.roboflow.com).
3. **Fine-tune YOLOv8** on SCVD or a weapon dataset, then set `YOLO_MODEL=runs/detect/train/weights/best.pt`.

---

## API endpoints

- `GET /api/health` — status + `app_mode`
- `GET /api/settings` / `PUT /api/settings` — thresholds, mode, cooldown
- `POST /api/dispatch` — trigger email/SMS/call after user confirmation
- `GET /api/dispatch/log` — dispatch history
- `WS /ws/live` — frame analysis + `hazard_alert` events

---

## Testing setup guide (downloadable)

- **Markdown:** [docs/GuardianAI-Testing-Setup-Guide.md](docs/GuardianAI-Testing-Setup-Guide.md)
- **Print / PDF:** open [docs/GuardianAI-Testing-Setup-Guide.html](docs/GuardianAI-Testing-Setup-Guide.html) in a browser → Print → Save as PDF

---

## Test plan (test mode)

1. Start backend + frontend; confirm **Demo / Test Mode** in header.
2. Set `TEST_EMAIL` and SMTP in `backend/.env`.
3. Start webcam; point at a **knife** (or printed image) — wait for 5 consecutive confident frames.
4. Modal should show hazard type, snapshot, 10s countdown; click **Confirm & Dispatch** or wait for auto-dispatch.
5. Check your test inbox for LLM-composed email with JPEG attachment.
6. Verify `backend/dispatch_log.json` has `mode: "test"`.
7. Repeat with **gun/fire/lighter** props or Roboflow-enabled models.
8. Click **False Alarm** — no dispatch should occur if countdown not finished (if dismissed before dispatch).
9. Enable **Real Mode** only when authorized; confirm cooldown blocks rapid repeat dispatches.

---

## License

Apache-2.0 — see [LICENSE](LICENSE). Use emergency integrations responsibly.
