# Render Deployment

This app is a Django service, so it cannot run on GitHub Pages. Keep `jadensingh.com` on GitHub Pages and deploy this app to a subdomain such as:

```text
guide.jadensingh.com
```

## What Is Already Configured

- `render.yaml` blueprint for a free Render web service
- `build.sh` for installing dependencies and collecting static files
- `gunicorn` start command
- Database migrations run in the Render start command because free tier services do not support `preDeployCommand`
- `whitenoise` static file serving
- `dj-database-url` production database configuration
- Environment-driven `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `DATABASE_URL`
- `.python-version` pinned to Python `3.13.5`

## Deploy Steps

1. Push this project to a GitHub repository.
2. Create a free PostgreSQL database with an external provider such as Neon.
3. Copy the external database connection string. It should look like `postgresql://...`.
4. In Render, choose **New +** -> **Blueprint**.
5. Connect the GitHub repository.
6. Render should detect `render.yaml`.
7. Render will ask for the unsynced `DATABASE_URL` environment variable. Paste the external Postgres connection string.
8. Create the blueprint.
9. Wait for the first deploy to finish.
10. Open the generated `*.onrender.com` URL.

The blueprint uses Render's `free` web service plan and does not create a paid Render database.

On Render's free tier, migrations run each time the service starts:

```bash
python manage.py migrate --no-input && gunicorn summitguide.wsgi:application
```

That is acceptable for this prototype. If you later move to a paid Render service, move migrations back to `preDeployCommand`.

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

On Render's free plan, the web service may sleep when idle. Long imports may be more reliable as one-off jobs if Render offers that option for your account. If an import stops midway, rerun the command; it is designed to update existing records.

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

## External Postgres

For a no-charge setup, use Neon or another external free Postgres provider.

In Neon:

1. Create a project.
2. Create or use the default database.
3. Copy the pooled or direct connection string.
4. Paste it into Render as `DATABASE_URL`.

Do not use SQLite on Render. Render instances have ephemeral filesystems, so SQLite data can disappear between deploys/restarts.

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
