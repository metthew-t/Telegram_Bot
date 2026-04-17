# Counselling Platform (Telegram Bot + Web Dashboard)

A full-stack anonymous counselling system enabling users to submit and manage support cases via a **Telegram bot**, while admins and owners handle cases through a modern **React web dashboard**.

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [User Roles](#user-roles)
- [Features](#features)
- [Setup & Installation](#setup--installation)
- [Running the Project](#running-the-project)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Telegram    │     │  Django Backend   │     │  React Frontend  │
│  Bot (User)  │◄───►│  (REST API)      │◄───►│  (Admin/Owner)   │
│              │     │                  │     │                  │
│  /newcase    │     │  JWT Auth        │     │  Dashboard       │
│  /mycases    │     │  Role Permissions│     │  Case Management │
│  /reply      │     │  Audit Logging   │     │  User Management │
│  /viewcase   │     │  Notifications   │     │  Audit Logs      │
└──────────────┘     └──────────────────┘     └──────────────────┘
                              │
                     ┌────────┴────────┐
                     │   PostgreSQL    │
                     │   (or SQLite)   │
                     └─────────────────┘
```

---

## Tech Stack

| Layer      | Technology                                           |
|------------|------------------------------------------------------|
| Backend    | Python, Django 4.2+, Django REST Framework           |
| Auth       | djangorestframework-simplejwt (JWT)                  |
| Database   | PostgreSQL (production) / SQLite (development)       |
| Frontend   | React 18, Vite, Axios, React Router 6               |
| Bot        | python-telegram-bot 20.5+                            |
| Other      | django-cors-headers, requests                        |

---

## User Roles

| Role    | Access                | Identity Visibility        |
|---------|----------------------|----------------------------|
| **Owner** | Web dashboard, all data | Sees all identities        |
| **Admin** | Web dashboard, assigned cases | Cannot see user/owner IDs |
| **User**  | Telegram bot only     | Cannot see admin/owner IDs |

---

## Features

### Telegram Bot
- `/start` — Register and get started
- `/newcase` — Multi-step case creation (title → description → confirm)
- `/mycases` — List all your cases with status indicators
- `/viewcase` — View messages on a specific case
- `/reply` — Step-by-step reply to a case
- `/message` — Legacy single-line reply format
- Real-time Telegram notifications on case updates

### Web Dashboard
- **Login/Register** — JWT-based authentication
- **Dashboard** — View and create cases
- **Admin Panel** — Search, filter, and manage all cases
- **Case Detail** — Message thread with 10-second auto-refresh
- **User Management** (Owner only) — Browse all users/admins
- **Audit Logs** (Owner only) — Track all platform actions
- Case assignment and reassignment controls
- Role-based field visibility

### Security
- JWT with 5-minute access tokens and 1-day refresh tokens
- Automatic token refresh on expiry
- Token blacklisting on rotation
- Role-based API permissions
- No identity leaks between user/admin roles
- CORS configured per environment

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (optional — SQLite works for development)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Telegram_Bot.git
cd Telegram_Bot
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt

# Create .env or set environment variables (see below)

# Run migrations
python manage.py migrate

# Create a superuser (owner)
python manage.py createsuperuser

# (Optional) Set the superuser's role to 'owner' via Django admin or shell:
python manage.py shell -c "
from counselling.models import User
u = User.objects.get(username='your_username')
u.role = 'owner'
u.save()
print('Done')
"
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/botfather) on Telegram
2. Copy the bot token
3. Set the `TELEGRAM_BOT_TOKEN` environment variable

---

## Running the Project

### Backend (Django)

```bash
cd backend

# For SQLite (development)
set USE_SQLITE=1        # Windows
export USE_SQLITE=1     # macOS/Linux

python manage.py runserver
```

The API will be available at `http://localhost:8000`.

### Frontend (React + Vite)

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### Telegram Bot

```bash
# Set environment variables first
set TELEGRAM_BOT_TOKEN=your-token-here   # Windows
set BACKEND_URL=http://localhost:8000     # Windows

export TELEGRAM_BOT_TOKEN=your-token-here  # macOS/Linux
export BACKEND_URL=http://localhost:8000    # macOS/Linux

python bot/telegram_bot.py
```

---

## Environment Variables

| Variable             | Required | Default                  | Description                        |
|----------------------|----------|--------------------------|------------------------------------|
| `TELEGRAM_BOT_TOKEN` | Yes      | —                        | Token from BotFather               |
| `BACKEND_URL`        | No       | `http://localhost:8000`  | Backend API URL for the bot        |
| `USE_SQLITE`         | No       | `0`                      | Set to `1` to use SQLite           |
| `VITE_API_URL`       | No       | `http://localhost:8000`  | Backend URL for the frontend       |
| `SECRET_KEY`         | Prod     | (insecure default)       | Django secret key                  |
| `DEBUG`              | Prod     | `True`                   | Set to `False` in production       |

See `.env.example` for a template.

---

## API Endpoints

### Authentication
| Method | Endpoint                | Auth     | Description              |
|--------|------------------------|----------|--------------------------|
| POST   | `/api/login/`          | No       | Get JWT tokens           |
| POST   | `/api/telegram-login/` | No       | Authenticate via Telegram ID |
| POST   | `/api/token/refresh/`  | No       | Refresh access token     |
| GET    | `/api/profile/`        | Yes      | Current user profile     |

### Users
| Method | Endpoint        | Auth     | Description              |
|--------|----------------|----------|--------------------------|
| GET    | `/api/users/`  | Owner    | List all users           |
| POST   | `/api/users/`  | No       | Register new user        |
| GET    | `/api/users/{id}/` | Owner/Self | User detail          |

### Cases
| Method | Endpoint                     | Auth        | Description            |
|--------|------------------------------|-------------|------------------------|
| GET    | `/api/cases/`                | Yes         | List cases (filtered by role) |
| POST   | `/api/cases/`                | Yes         | Create a new case      |
| GET    | `/api/cases/{id}/`           | Yes         | Case detail            |
| POST   | `/api/cases/{id}/assign/`    | Admin/Owner | Assign admin to case   |
| POST   | `/api/cases/{id}/close/`     | Yes         | Close a case           |

### Messages
| Method | Endpoint                | Auth     | Description              |
|--------|------------------------|----------|--------------------------|
| GET    | `/api/messages/`       | Yes      | List messages (filter by `?case=`) |
| POST   | `/api/messages/`       | Yes      | Send a message           |

### Audit Logs
| Method | Endpoint             | Auth     | Description              |
|--------|---------------------|----------|--------------------------|
| GET    | `/api/audit-logs/`  | Owner    | List all audit logs      |

---

## Testing

### Backend Tests

```bash
cd backend
set USE_SQLITE=1
python manage.py test counselling -v2
```

Tests cover:
- User registration
- JWT login
- Owner/admin permissions
- Case creation and assignment
- Message permissions
- Telegram login flow
- Profile endpoint

### Frontend Build Verification

```bash
cd frontend
npm run build
```

---

## Deployment

### Using Docker

```bash
# Build and start all services
docker-compose up --build

# Services:
# - Backend:  http://localhost:8000
# - Frontend: http://localhost:5173
# - Bot:      runs automatically
# - Postgres: port 5432
```

### Manual Deployment (Heroku/Railway/Render)

1. Set all environment variables in your platform's dashboard
2. Use `requirements.txt` for Python dependencies
3. Set `USE_SQLITE=0` and configure `DATABASE_URL`
4. Build the frontend: `cd frontend && npm run build`
5. Serve the built frontend via a static file server or CDN

---

## Production Monitoring (Render)

If you are using **Render's Free Tier**, the server will spin down after 15 minutes of inactivity, causing delays in Telegram bot responses.

To prevent this:
1. Use a free monitoring service like [UptimeRobot](https://uptimerobot.com/).
2. Create a new "HTTP(s)" monitor.
3. Point it to your service's health endpoint: `https://your-app-name.onrender.com/health/`
4. Set the monitoring interval to **10 minutes**.

This will keep the service "awake" and ensure the bot responds instantly.

---

## Project Structure

```
Telegram_Bot/
├── backend/
│   ├── counselling/           # Django app
│   │   ├── models.py          # User, Case, Message, AuditLog
│   │   ├── views.py           # ViewSets, permissions, auth views
│   │   ├── serializers.py     # Role-based serialization
│   │   ├── urls.py            # API routes
│   │   ├── admin.py           # Django admin registration
│   │   └── tests.py           # Unit tests
│   ├── counselling_platform/  # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── manage.py
├── bot/
│   └── telegram_bot.py        # Telegram bot with ConversationHandlers
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Routes, navigation, auth state
│   │   ├── api.js             # Axios instance, interceptors, helpers
│   │   ├── auth.js            # Token storage utilities
│   │   ├── main.jsx           # React entry point
│   │   ├── styles.css         # Design system & component styles
│   │   └── pages/
│   │       ├── Login.jsx
│   │       ├── Register.jsx
│   │       ├── Dashboard.jsx
│   │       ├── CaseDetail.jsx
│   │       ├── AdminDashboard.jsx
│   │       ├── UserManagement.jsx
│   │       └── AuditLogs.jsx
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## License

This project is for educational and private use.
