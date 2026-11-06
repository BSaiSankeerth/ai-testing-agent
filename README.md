# AI Testing Agent

An autonomous software testing platform. You give it a website URL and plain-English testing instructions. A team of AI agents plans the tests, explores the site in a real browser, writes test cases, executes them with Playwright, judges the results from recorded evidence, and files structured bug reports.

> Built as a full-stack portfolio project: LangGraph multi-agent orchestration, tool-restricted browser automation, validated LLM output, FastAPI, PostgreSQL and React.

## Screenshots

| Dashboard | Live progress |
|---|---|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Live progress](docs/screenshots/live-progress.png) |

| Results with evidence | Bug report |
|---|---|
| ![Results](docs/screenshots/results.png) | ![Bug report](docs/screenshots/bug-report.png) |

## How it works

```
User -> React dashboard -> FastAPI -> LangGraph workflow
                                         |
   Planning -> Exploration -> Test generation -> Execution -> Analysis -> Bug reporting
                                         |
                              Playwright (guarded browser)
                                         |
                                  Target web app
```

| Agent | Job |
|---|---|
| Planning | Turns the instructions into a structured test plan |
| Exploration | Crawls the site in a browser and records real elements with verified, unique selectors (no LLM, so it cannot invent selectors) |
| Test generation | Writes one test case per plan task, using only selectors found during exploration. Code verifies every selector afterwards |
| Execution | Runs each case in a fresh browser session through approved tools only, recording per-case evidence |
| Result analysis | Compares expected and actual behaviour. Judges by evidence (HTTP status, page text, validation messages), not by guessed URLs or wording |
| Bug reporting | Writes a structured report for failed cases only. Reproduction steps are built by code from the real test steps |

## Key design decisions

- **The LLM never runs code.** Test steps are a closed set (`goto`, `fill`, `click`, `expect_text`, `expect_url_contains`), enforced by Pydantic schemas.
- **Credentials never reach the LLM.** Test data uses placeholders such as `{{valid_password}}`. Each run registers its own throwaway account, resolved only inside the execution step.
- **Every LLM output is validated** with Pydantic, with a retry on invalid output.
- **Automation errors are never reported as app bugs.** Results can be `passed`, `failed`, `inconclusive`, `blocked`, `error` or `not_run`. Dropped scenarios are shown as `not_run` with the reason, never hidden.
- **Deterministic guards sit around the model.** For example, a successful positive flow cannot be marked failed because of a guessed redirect URL.
- **Verified against a planted defect.** A deliberately broken login in the demo shop was detected and reported with correct evidence.

## Security

- Browser navigation is restricted to approved origins (`APPROVED_TARGETS`, `APPROVED_API_ORIGINS`). Every request, including redirects and background calls, passes the URL guard. Other localhost ports, cloud metadata addresses and `file://` URLs are blocked.
- Clicks on destructive-looking controls (pay, delete, buy now) require explicit approval.
- Action limits and timeouts on every browser session. One run at a time.
- JWT authentication with argon2 password hashing. Each user sees only their own sessions and evidence.
- Screenshot serving is ownership-checked and confined to `storage/screenshots`.
- Secrets live in `.env` (git-ignored). The API key and JWT secret are masked in logs.

## Tech stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL
**AI:** LangGraph, Groq API (modular LLM interface, model set in `.env`)
**Browser:** Playwright (Chromium)
**Frontend:** React, Vite, Tailwind CSS, Axios, React Router

## Project structure

```
backend/app/
  agents/     LangGraph workflow, one module per agent
  api/        REST routes (auth, sessions, results, health)
  browser/    Playwright manager, URL guard, inspector, approved tools
  core/       settings and security helpers
  db/         engine, session, ORM models
  llm/        provider-neutral interface + Groq client
  schemas/    Pydantic schemas (API and LLM output)
  services/   run persistence, background runner, progress
backend/alembic/   database migrations
frontend/src/      dashboard (pages, components, API client)
```

## Getting started (Windows PowerShell)

### Prerequisites

- Python 3.12 (3.14 may lack prebuilt packages), Node.js 20+, PostgreSQL, Git
- A Groq API key
- A web app you own to test. This repo does not include one

### 1. Clone

```powershell
git clone https://github.com/BSaiSankeerth/ai-testing-agent.git
cd ai-testing-agent
```

### 2. Database

Create an empty PostgreSQL database (for example `ai_testing_agent`).

### 3. Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
Copy-Item .env.example .env
```

Edit `backend\.env` and set at least:

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://USER:PASSWORD@localhost:5432/ai_testing_agent` |
| `GROQ_API_KEY` | Your Groq key |
| `LLM_MODEL` | A chat model available to your key |
| `JWT_SECRET` | Long random string: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `APPROVED_TARGETS` | JSON list of sites the agent may test, for example `["http://localhost:3000"]` |
| `APPROVED_API_ORIGINS` | JSON list of the target's API origins, for example `["http://localhost:8000"]` |
| `BROWSER_HEADLESS` | `false` to watch the browser, `true` for servers |
| `BROWSER_SLOW_MO_MS` | Delay between actions in ms (for example `600` when watching) |

Create the tables and start the API:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --port 8001
```

API docs: http://localhost:8001/docs

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5174, register an account, then create a testing session.

### 5. Run a test

1. Start the web app you want to test.
2. Click **New session**, enter its URL and instructions, for example:
   *Test the registration and login functionality. Verify valid registration, duplicate email registration, invalid email, empty fields, successful login, and incorrect password.*
3. Watch the stage tracker and per-case verdicts. Open **View evidence** on any case for the screenshot, network calls and page text.

## Known limitations

- Free-tier LLM quotas can interrupt runs. Affected cases are recorded as `not_run` or `inconclusive`, never guessed.
- Created test accounts remain in the target app's database.
- One run at a time.
- LLM output varies between runs, so the generated test cases can differ.
- The token is stored in `localStorage`, which is acceptable locally but not ideal for production.
- Only tested end to end against one demo e-commerce site, focused on registration and login flows.

## Roadmap

Regression testing, API testing, visual comparison, GitHub Issues integration, Docker deployment, automated test suite.

## Disclaimer

Only test websites you own or are authorized to test. Use dedicated test accounts and synthetic data, and never run against real payments.
