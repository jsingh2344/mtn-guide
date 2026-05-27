# Render Deployment

This app is a Django service, so it cannot run on GitHub Pages. Keep `jadensingh.com` on GitHub Pages and deploy this app to a subdomain such as:

```text
guide.jadensingh.com
```

## What Is Already Configured

- `render.yaml` blueprint for a Render web service and PostgreSQL database
- `build.sh` for installing dependencies and collecting static files
- `gunicorn` start command
- `whitenoise` static file serving
- `dj-database-url` production database configuration
- Environment-driven `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `DATABASE_URL`
- `.python-version` pinned to Python `3.13.5`

## Deploy Steps

1. Push this project to a GitHub repository.
2. In Render, choose **New +** -> **Blueprint**.
3. Connect the GitHub repository.
4. Render should detect `render.yaml`.
5. Review the proposed web service and PostgreSQL database.
6. Create the blueprint.
7. Wait for the first deploy to finish.
8. Open the generated `*.onrender.com` URL.

The blueprint uses a `starter` web service and a `basic-256mb` PostgreSQL database. You can lower or raise those in Render before creating the service if you want.

## Create A Production Admin

Open the Render dashboard for the web service.

Use **Shell** if available, or create a one-off job, and run:

```bash
python manage.py createsuperuser
```

## Import Data In Production

Run these commands from Render Shell or one-off jobs:

```bash
python manage.py scrape_summitpost_wyoming
python manage.py scrape_summitpost_peru
```

These commands fetch live SummitPost pages, so they can take several minutes.

## Custom Domain

In Render:

1. Open the web service.
2. Go to **Settings** -> **Custom Domains**.
3. Add `guide.jadensingh.com`.
4. Render will show a DNS target.

In your DNS provider for `jadensingh.com`:

1. Add a `CNAME` record.
2. Name/host: `guide`
3. Value/target: the Render hostname shown in the dashboard.

Keep the existing GitHub Pages DNS records for `jadensingh.com` unchanged.

## Important Settings

The `render.yaml` currently includes:

```text
ALLOWED_HOSTS=mountain-guide.onrender.com,guide.jadensingh.com
CSRF_TRUSTED_ORIGINS=https://mountain-guide.onrender.com,https://guide.jadensingh.com
```

If Render creates a different default hostname, update those environment variables in Render.

## Local Production Check

You can still run locally with SQLite:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

For production-like checks:

```powershell
$env:DEBUG="False"
$env:ALLOWED_HOSTS="127.0.0.1,localhost"
$env:CSRF_TRUSTED_ORIGINS="http://127.0.0.1:8000,http://localhost:8000"
.\.venv\Scripts\python.exe manage.py check --deploy
```
