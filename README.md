# Pi Zero W Productivity Dashboard

A green-on-black hacker-themed TUI dashboard running on a Raspberry Pi Zero W with a Waveshare 3.5" SPI LCD. Displays Google Calendar events and Notion daily goals at a glance, with buzzer alarms to keep you on track.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20Zero%20W-red)
![Display](https://img.shields.io/badge/Display-Waveshare%203.5%22%20SPI%20LCD-green)
![TUI](https://img.shields.io/badge/TUI-Textual-brightgreen)

## Features

- **Google Calendar** — Shows next 5 upcoming events with date, time, and title
- **Notion Daily Goals** — Pulls goals from a Notion database with optional alarm times shown in brackets
- **Buzzer Alarms** — Passive buzzer on GPIO 12 fires two 1-second beeps at scheduled times
  - Fixed times: `08:30`, `14:00`
  - Intervals: `every 2h`, `every 30m`, `every 1h30m`
- **Auto-refresh** — Updates data every 5 minutes
- **Tap to Refresh** — Touch the screen to trigger an immediate refresh
- **Auto-start on Boot** — Runs as a systemd service on tty1

## Hardware

| Component | Details |
|-----------|---------|
| Board | Raspberry Pi Zero W (armv6l) |
| Display | Waveshare 3.5" SPI LCD (480x320, ili9486) |
| Touchscreen | ADS7846 on `/dev/input/event0` |
| Buzzer | Passive buzzer on GPIO 12 (Pin 32) |
| Font | Terminus Bold 20x10 |

## Project Structure

```
main.py                  — Entry point, loads .env and starts the Textual app
services/
  calendar_service.py    — Google Calendar API (OAuth, token.json)
  notion_service.py      — Notion API (goals + alarm times, cached for buzzer)
  buzzer_service.py      — GPIO 12 buzzer, fixed times & interval alarms
  touch_service.py       — Touchscreen tap → refresh via call_from_thread
ui/
  dashboard_app.py       — Textual App, two vertical panels
  dashboard.tcss         — Green-on-black hacker theme
deploy_pi.py             — SSH/SFTP deployment script (local network only)
check_pi.py              — SSH status checker
```

## Layout

```
╭──────────────────────────╮
│  UPCOMING EVENTS         │
│  [Mar 22 10:00 AM] ...   │
│  [Mar 22  2:00 PM] ...   │
╰──────────────────────────╯
╭──────────────────────────╮
│  DAILY GOALS             │
│  • Goal one [08:00]      │
│  • Goal two [every 2h]   │
│  • Goal three            │
╰──────────────────────────╯
```

## Setup

### Prerequisites

- Raspberry Pi Zero W with Raspbian (Debian Bookworm/Trixie)
- Waveshare 3.5" SPI LCD ([driver setup](https://github.com/waveshare/LCD-show))
- Python 3.11+
- Google Calendar API credentials (`credentials.json`)
- Notion integration token and goals database ID

### 1. Clone the Repository

```bash
git clone https://github.com/Robiul2015/pi-dashboard.git
cd pi-dashboard
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
NOTION_TOKEN=your_notion_integration_token
NOTION_GOALS_DATABASE_ID=your_goals_db_id
GOOGLE_CREDENTIALS_PATH=credentials.json
```

### 3. Google Calendar OAuth

On your local machine (not the Pi), run the OAuth flow to generate `token.json`:

```bash
pip install google-api-python-client google-auth-oauthlib
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file('credentials.json',
    ['https://www.googleapis.com/auth/calendar.readonly'])
creds = flow.run_local_server(port=0)
with open('token.json', 'w') as f:
    f.write(creds.to_json())
"
```

Upload the generated `token.json` to the Pi's project directory.

### 4. Notion Database

Create a Notion database with these properties:

| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Goal name |
| Alarm | Text | Optional. `HH:MM` for fixed time or `every Xh`, `every Xm`, `every XhYm` for intervals |

Share the database with your Notion integration.

### 5. Install on Pi

#### Option A: Using the deploy script

From your local machine (Windows/Mac/Linux):

```bash
pip install paramiko
python deploy_pi.py
```

This uploads all project files via SFTP, creates the venv, and installs dependencies.

#### Option B: Manual setup

```bash
# On the Pi
cd ~/pi-dashboard
python3 -m venv venv --system-site-packages
./venv/bin/pip install -r requirements.txt
```

### 6. Systemd Service

Create `/etc/systemd/system/pi-dashboard.service`:

```ini
[Unit]
Description=Pi Dashboard (Textual TUI)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
SupplementaryGroups=input
WorkingDirectory=/home/pi/pi-dashboard
ExecStart=/home/pi/pi-dashboard/venv/bin/python3 /home/pi/pi-dashboard/main.py
Environment=TERM=linux
StandardInput=tty
StandardOutput=tty
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-dashboard
sudo systemctl start pi-dashboard
```

### 7. Display Configuration

In `/boot/firmware/config.txt`:

```ini
dtparam=spi=on
dtoverlay=waveshare35a
# Disable vc4-kms-v3d (conflicts with fbtft)
```

In `/boot/firmware/cmdline.txt`, append:

```
fbcon=map:10
```

In `/etc/rc.local` (before `exit 0`):

```bash
con2fbmap 1 1
```

Disable getty on tty1 so the dashboard owns the screen:

```bash
sudo systemctl disable getty@tty1
```

## Buzzer Wiring

```
Pi Zero W          Passive Buzzer
─────────          ──────────────
GPIO 12 (Pin 32) → + (Signal)
GND     (Pin 34) → - (Ground)
```

## Deploy Workflow

After making local changes:

```bash
# Quick deploy (uploads changed files, restarts service)
python deploy_pi.py

# Check Pi status
python check_pi.py
```

Or manually:

```bash
# Upload specific files
scp services/notion_service.py pi@<PI_IP>:~/pi-dashboard/services/
ssh pi@<PI_IP> "sudo systemctl restart pi-dashboard"
```

## Dependencies

| Package | Purpose |
|---------|---------|
| [textual](https://github.com/Textualize/textual) | TUI framework |
| [google-api-python-client](https://github.com/googleapis/google-api-python-client) | Google Calendar API |
| [google-auth-oauthlib](https://github.com/googleapis/google-auth-library-python-oauthlib) | OAuth2 authentication |
| [notion-client](https://github.com/ramnes/notion-sdk-py) | Notion API |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable loading |

> **Note:** On Pi Zero W, use `--system-site-packages` for the venv to leverage apt-installed `cryptography` and piwheels prebuilt wheels. Avoid compiling packages from source.

## License

MIT
