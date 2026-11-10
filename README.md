# Censor

A FastAPI backend that automatically censors profanity in audio files. You upload a voice note, it gets transcribed with word-level timestamps, flagged words are detected, and you get back a new audio file where those words are replaced by a beep, silence, or a sound effect of your choice. It can also export the transcription as an `.srt` subtitle file with the flagged words masked.

## How it works

```
Client ──► FastAPI ──► PostgreSQL (status, transcription, credits)
              │
              ├──► Cloudflare R2 (original and censored audio)
              │
              └──► Redis ──► Celery worker
                               1. transcribe   (WhisperX on Replicate, word-level alignment)
                               2. detect       (better-profanity + the user's own word list)
                               3. render       (pydub: beep, silence or sound effect)
```

Audio processing takes several seconds, so the API never does it inside the request. `POST /audio/` validates the file, uploads it to storage, saves a `pending` row and pushes a chain of three Celery tasks. The client then polls `GET /audio/{id}` until the status becomes `completed` or `failed`.

Splitting the pipeline into three tasks means that changing the censoring options does not redo the whole job: a new word list only reruns detection and rendering, and switching from a beep to a sound effect only reruns rendering.

## Features

- Upload of `mp3`, `wav`, `ogg`, `m4a`, `flac`, `aac` and `webm` files, validated by decoding them (not just by extension), with size and duration limits
- Word-level transcription and alignment with WhisperX
- Profanity detection with a default dictionary plus a custom word list per audio
- Three censoring modes: beep, silence, or a custom sound effect uploaded by the user
- `.srt` subtitle export with configurable masking (`f***`, `fu##`...)
- Credit system: each user starts with 50 credits, processing costs credits per second of audio, and credits can be bought through Polar checkout
- Authentication with PropelAuth, users synced to the database through a signed webhook
- Signed webhook verification for both Polar and PropelAuth
- Database migrations with Alembic

## Tech stack

| Layer | Tools |
|---|---|
| API | FastAPI, Pydantic, SQLModel |
| Database | PostgreSQL (asyncpg in the API, psycopg2 in the worker), Alembic |
| Background jobs | Celery, Redis |
| Audio | WhisperX (via Replicate), pydub, FFmpeg, better-profanity |
| Storage | Cloudflare R2 (S3 API through boto3) |
| Auth and payments | PropelAuth, Polar, Svix |
| Tooling | uv, poethepoet, Scalar API docs |

## Project structure

```
app/
├── main.py              # FastAPI app, CORS, docs
├── api/
│   ├── routers/         # audio, sound effects, user, checkout and webhooks
│   ├── schemas/         # request and response models
│   ├── dependencies.py  # auth, services, Polar client
│   └── audio_file.py    # upload validation
├── service/             # business logic (audio, users, credits, sound effects)
├── worker/
│   ├── tasks.py         # Celery tasks
│   └── audio_censor.py  # transcription, detection and rendering
├── database/            # models and async session
├── config/              # settings split between API, worker and shared
├── core/exceptions.py   # custom HTTP errors
└── object_storage.py    # R2 client
migrations/              # Alembic revisions
```

## Getting started

### Prerequisites

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis
- FFmpeg available in your `PATH` (used by pydub)
- Accounts on Replicate, Cloudflare R2, PropelAuth and Polar (sandbox works)

### Configuration

Copy `.env.example` to `.env` and fill in your own values.

### Database

```bash
uv run alembic upgrade head
```

### Run

The API and the worker run as two separate processes.

```bash
# API
uv run fastapi dev

# Worker
uv run poe worker
```

The worker uses `--pool=solo` so that it also runs on Windows. On Linux or WSL you can remove it to process several tasks in parallel.

Interactive API docs are available at `http://localhost:8000/docs` when `ENABLE_DOCS=true`.

### Webhooks in local development

Polar and PropelAuth need to reach your machine to send webhooks. The simplest way is VS Code port forwarding: open the **Ports** panel, forward port `8000`, then right-click it and set **Port Visibility** to **Public** (a private port asks for a GitHub login, which webhooks can't do). Any other tunnel (ngrok, Cloudflare Tunnel...) works too.

Register these URLs in each dashboard:

- `https://<your-tunnel>/webhooks/polar`, with the `order.paid` event
- `https://<your-tunnel>/webhooks/propelauth`, with the `user.created` event

## API overview

| Method | Route | Description |
|---|---|---|
| `GET` | `/me` | Current user and credit balance |
| `POST` | `/user/checkout` | Create a Polar checkout to buy credits |
| `POST` | `/audio/` | Upload an audio file and start processing |
| `GET` | `/audio/` | List the user's audio files |
| `GET` | `/audio/{id}` | Get one audio file and its status |
| `PATCH` | `/audio/{id}` | Change the censoring options and re-render |
| `GET` | `/audio/{id}/download` | Get a temporary download link for the censored file |
| `POST` | `/audio/{id}/subtitle` | Export the transcription as `.srt` |
| `POST` | `/sfx/` | Upload a custom sound effect |
| `GET` | `/sfx/` | List the user's sound effects |

## Credits

| Action | Cost |
|---|---|
| New upload (transcription, detection and rendering) | 3 credits per second of audio |
| New word list (detection and rendering) | 2 credits per second |
| New censoring mode (rendering only) | 1 credit per second |

New users get 50 free credits. One credit is bought for one euro cent.