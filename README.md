# Telegram_Bot

## Backend

The Django backend is located under `backend/`.

API endpoints:
- `POST /api/users/` - register a new user
- `POST /api/login/` - get JWT access and refresh tokens
- `POST /api/telegram-login/` - authenticate a Telegram user by `telegram_id`
- `POST /api/token/refresh/` - refresh JWT access tokens
- `GET /api/profile/` - fetch the authenticated user's profile
- `CRUD /api/cases/` - manage support cases
- `CRUD /api/messages/` - send and read case messages

## Telegram Bot

The bot implementation is in `bot/telegram_bot.py`.

Environment variables:
- `TELEGRAM_BOT_TOKEN` - bot token from BotFather
- `BACKEND_URL` - base URL for the Django backend (default: `http://localhost:8000`)

Commands supported:
- `/start`
- `/newcase <title> | <description>`
- `/mycases`
- `/message <case_id> | <message>`

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running backend

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

## Running Telegram bot

```bash
export TELEGRAM_BOT_TOKEN="<your-token>"
export BACKEND_URL="http://localhost:8000"
python bot/telegram_bot.py
```
