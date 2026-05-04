# AGENTS.md

## Project Overview

This repository is a Django 5.2 project for a Telegram bot that sends daily *A COURSE IN MIRACLES* workbook lessons. The active app is `lessons`; `ucdm_bot` contains Django project settings; `acim_workbook` contains lesson markdown content in `es` and `en`; `marto_python` is a local utility package used by the project.

The bot uses `python-telegram-bot` v22 async APIs, SQLite for local persistence, and secrets from `secrets.toml` or environment variables.

## Important Paths

- `ucdm_bot/settings.py`: Django settings, Telegram/email secrets, database, logging.
- `lessons/models.py`: `Chat` model tracking Telegram chat state.
- `lessons/bot.py`: lesson sending logic, send cadence checks, Telegram message splitting.
- `lessons/bot_updates.py`: Telegram command handlers and conversation state.
- `lessons/bot_loop.py`: polling loop and periodic send-all loop.
- `lessons/workbook.py`: workbook file loading and day-to-lesson mapping.
- `acim_workbook/workbook_structure.json`: ordered lesson file groups.
- `acim_workbook/es`, `acim_workbook/en`: lesson markdown files.
- `marto_python/secrets.py`: secret loading helper.

## Environment

- Python requirement is `>=3.13`.
- Dependencies are managed with `uv` and declared in `pyproject.toml` / `uv.lock`.
- Activate virtual environment before running commands with:

```bash
source .venv/bin/activate
```

## Secrets And Local State

Do not commit or print secret values. This project reads sensitive values from `secrets.toml` or environment variables.

## Development Commands

- Run the bot polling loop locally only when Telegram credentials are configured:

```bash
./ucdm.py
```

ucdm.py has a shebang that specifies the django settings module

## Coding Conventions

- Follow the existing compact Python style: small module-level async functions, single quotes, and minimal comments.
- Keep Telegram interaction code async. Use Django async ORM calls (`afirst`, `asave`, async iteration) in bot paths.
- Keep lesson numbers internally 0-based and user-facing lesson numbers 1-based.
- Respect Telegram's 4096-character message limit; use or update `split_for_telegram` instead of sending long text directly.
- Avoid changing workbook markdown content unless the task is specifically about lesson text or structure.
- Avoid broad refactors in `marto_python`; it is a shared local utility package and much of it is unrelated to this bot.

## Operational Notes

- Production-like behavior is controlled by `PRODUCTION=true`.
- `ucdm.py` sets `DJANGO_SETTINGS_MODULE=ucdm_bot.settings` and starts `lessons.bot_loop.run_bot_loop()`.
- The send loop checks every 5 minutes and sends lessons only between 08:00 and 23:00 local server time.
- Calendar mode maps January 1 to lesson 1 and clamps leap-year day 366 to lesson 365.
- Non-calendar mode advances from `Chat.last_lesson_sent`.

## Known Code Caveats

- `lessons/bot_updates.py` references `LessonType.OWN`, but `LessonType` defines `FIRST`, `CALENDAR`, and `OTHER`. Be careful around this branch if editing lesson-mode flow.
- `lessons/workbook.py` caches workbook content process-wide by language and day. Tests that mutate workbook files need to clear `workbook_cache` and possibly `workbook_structure`.
