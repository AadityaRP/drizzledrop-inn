# Deployment Guide (Drizzle Drop Inn)

## Local (Windows)
1. Install Python 3.12 and MySQL 8.0 server.
2. Install GTK3 runtime for `weasyprint` support (required for PDF generation).
3. Create a virtual environment: `python -m venv venv`.
4. Activate the virtual environment: `venv\Scripts\activate`.
5. Install dependencies: `pip install -r requirements.txt`.
6. Copy `env.example` to `.env` and configure your database credentials.
7. Run migrations: `python manage.py migrate`.
8. Create a superuser: `python manage.py createsuperuser`.
9. Run the server: `python manage.py runserver`.

## Production (PaaS like Railway/Render)
1. Set environment variables from `env.example`.
2. Provision MySQL (8.x) and capture host/port/user/password/db.
3. Build command: `pip install -r requirements.txt`.
4. Start command: `gunicorn drizzledrop_inn.wsgi:application --bind 0.0.0.0:$PORT`.
5. Run migrations on deploy: `python manage.py migrate`.
6. Set `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` to your domain, and configure HTTPS at the platform.

## VPS (NGINX + Gunicorn)
1. Install Python 3.12, MySQL 8.x client libs.
2. Clone repo, create virtualenv, install requirements.
3. Export env vars or use a `.env` file loaded by systemd.
4. Run `python manage.py migrate` and `python manage.py collectstatic`.
5. Configure gunicorn systemd service:
   - ExecStart: `/path/venv/bin/gunicorn drizzledrop_inn.wsgi:application --bind 127.0.0.1:8000`
6. Configure Nginx to proxy requests to `127.0.0.1:8000` and serve static files. Enable HTTPS via Certbot.

## Data Seeding
After migrations, create the Chain Owner (superuser) and add the two hotels (City, Resort) plus room categories/rooms via the UI (Hotels > Add). Hotel Admin users should be linked via `HotelUser` assignments.
