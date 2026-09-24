# Prestige Pulse Cargo — CRM

Simple self-hosted CRM: Django + SQLite + Bootstrap 5 + Chart.js, single Docker container.

## Local installation

### Option A — Docker (recommended)

```bash
cp .env.example .env
# edit .env: set SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
docker compose up -d --build
```

Open http://localhost:8000 — log in with the admin credentials from `.env`.

Sample data (optional):

```bash
docker compose exec crm python manage.py seed_demo
```

### Option B — Python directly

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data/uploads data/exports data/backups
python manage.py migrate
python manage.py create_admin
python manage.py seed_demo      # optional
python manage.py runserver
```

Open http://localhost:8000.

## Persistent data

Everything lives in `DATA_DIR` (default `./data` locally, `/app/data` in Docker):

```
data/
├── database.sqlite3
├── uploads/
├── exports/
└── backups/
```

## Roles

- **Administrator** — manage all leads, users, imports/exports, dropdowns, backups.
- **Sales User** — see and update only leads they own or created; add follow-ups; personal dashboard.

Create users in **Users** (admins only). There is no public registration.

## Backups

- Admin → **Settings → Create Backup** produces `/data/backups/backup_YYYYMMDD_HHMMSS.zip` containing `database.sqlite3` + `uploads/`.
- Download from **Settings → View Backups**.

### Restore

```bash
docker compose stop crm
unzip data/backups/backup_YYYYMMDD_HHMMSS.zip -d data/
# overwrite data/database.sqlite3 and data/uploads/ with the archive contents
docker compose start crm
```

## Import / Export

- Admin → **Leads → Import** accepts `.xlsx` with at least a `name` column. Optional: `company, email, phone, stage, source, value, owner_username`.
- **Export XLSX** / **Export CSV** buttons on the Leads page.

## Dokploy deployment

1. Push this repo to Git.
2. In Dokploy: **New Application → Docker Compose**, connect repo.
3. Set environment variables from `.env.example`.
4. Add persistent volume mounted at **`/app/data`**.
5. Add domain `crm.pplcargo.com`.
6. Enable HTTPS (Let's Encrypt).
7. Deploy. On first boot, `entrypoint.sh` runs migrations and creates the admin from env vars.

## Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret (long random string) |
| `DEBUG` | `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hosts |
| `TIME_ZONE` | Default `Asia/Dubai` |
| `DATA_DIR` | Persistent data path (`/app/data`) |
| `ADMIN_NAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Initial admin account |

Never commit `.env`.