# Marzouki Production Deployment & Migration Guide (Hostinger VPS)

This guide takes the hardened build of the Marzouki Django e-commerce site
from local verification all the way to a production VPS deployment, plus a
safe path for the SQLite → PostgreSQL migration.

> **Read this entire document before touching production.** Every section
> includes a rollback path.

---

## 0. What's in this build (summary of changes)

| Area | Change |
|------|--------|
| Secrets | All keys/secrets now sourced from `.env` (none hard-coded). `.gitignore` blocks accidental commits. `.env.example` documents every variable. |
| Stripe | New signed webhook at `/stripe/webhook/`. Order is marked **paid** only by the webhook (with a transitional fallback while you set the secret). |
| Dashboard | Every URL wrapped in `staff_required` (login + `is_staff`). No anonymous access to admin tools. |
| Settings | New `TheProject/settings.py` with HTTPS, HSTS, secure cookies, CSRF trusted origins, Redis cache, rotating-file logging. |
| Pricing | One source of truth in `cart/pricing.py`. All money values use `Decimal`. N+1 fixed in the cart. |
| Models | `Order.user` and `OrderItem.storeitem` are now `SET_NULL` (no more deletion cascades that destroy order history). New snapshot fields. New indexes. |
| Frontend | Pagination fixed on `originals` / `prints` / `category`. SEO meta blocks added to `base.html`. Standalone `error.html`. |
| Deploy | New `requirements.txt`, `deploy/gunicorn.conf.py`, `deploy/marzouki.service`, `deploy/nginx.conf.example`. |

---

## 1. Backup Instructions (do this first, every time)

### 1.1 Code & config backup

```bash
# On the VPS, before pulling new code.
sudo cp -a /srv/marzouki /srv/marzouki.bak.$(date +%F-%H%M)
```

If you deploy via `git`, also tag the current commit so you can roll back
trivially:

```bash
cd /srv/marzouki
git tag -a "pre-hardening-$(date +%F)" -m "Snapshot before hardening rollout"
git push origin --tags
```

### 1.2 Database backup

**SQLite (current production):**

```bash
cd /srv/marzouki
# Hot backup with safe locking — Django can keep running.
sqlite3 db.sqlite3 ".backup '/srv/backups/db.sqlite3.$(date +%F-%H%M)'"
gzip /srv/backups/db.sqlite3.$(date +%F-%H%M)
```

**PostgreSQL (once you migrate):**

```bash
sudo -u postgres pg_dump -Fc marzouki > /srv/backups/marzouki-$(date +%F-%H%M).dump
```

Keep at least the last **7 daily** and **4 weekly** backups off-server
(e.g. push to Hostinger storage, S3, or a backup VPS).

### 1.3 Media backup

```bash
tar -czf /srv/backups/media-$(date +%F).tgz -C /srv/marzouki media
```

### 1.4 Rollback if a deployment goes wrong

```bash
# Stop the app
sudo systemctl stop marzouki

# Restore code
sudo rm -rf /srv/marzouki
sudo mv /srv/marzouki.bak.<timestamp> /srv/marzouki

# Restore DB
cd /srv/marzouki
gunzip -c /srv/backups/db.sqlite3.<timestamp>.gz > db.sqlite3

# Start the app
sudo systemctl start marzouki
```

---

## 2. Local Verification

Do this on your laptop **before** uploading anything.

### 2.1 Install + configure

```powershell
# Windows / PowerShell
python -m venv venv
venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# Create a local .env from the template:
copy .env.example .env
# Then edit .env with TEST Stripe keys (sk_test_..., pk_test_..., whsec_...)
# and DJANGO_DEBUG=True
```

### 2.2 Migrations & static

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input
```

If `makemigrations` proposes anything beyond the two new migrations shipped
in this build (`TheApp/0089_pricing_indexes_and_validators.py` and
`orders/0020_paid_at_snapshots_indexes.py`), **review carefully** — the
likely cause is the `Discount` model's `CheckConstraint`, which is
deliberately not auto-applied; you can accept the suggested migration only
after confirming no `Discount` row has both `section` and `item` NULL.

### 2.3 Run

```powershell
python manage.py runserver
```

Verify:

- `http://127.0.0.1:8000/` — home page loads.
- `http://127.0.0.1:8000/paints/` — catalog pages paginate.
- `http://127.0.0.1:8000/originals/` and `/prints/` — pagination buttons work.
- `http://127.0.0.1:8000/dashboard/admin_home/` — redirects to login if you
  log out; loads if you log in as staff.

### 2.4 Verify Stripe (local)

1. Run the Stripe CLI:

   ```bash
   stripe login
   stripe listen --forward-to localhost:8000/stripe/webhook/
   ```

   It prints a `whsec_...` value — put this in your local `.env` as
   `STRIPE_WEBHOOK_SECRET` and restart `runserver`.

2. Add a product to cart, check out with the Stripe test card `4242 4242 4242 4242`.

3. After the success page, look in the Stripe CLI output: you should see
   `checkout.session.completed` events delivered, and your Django log
   (`logs/app.log`) should print:

   ```
   payment.webhook: order #N marked paid
   ```

4. In the dashboard, open the order — `paid` should be `True`.

### 2.5 Verify dashboard authorization

In a fresh incognito window, try visiting:

- `/dashboard/admin_home/`
- `/dashboard/store_items/`
- `/dashboard/orders/`
- `/dashboard/sections/`

Every one of these should redirect you to `/login/`. Log in as a
non-staff user — you should be redirected away by `staff_member_required`.

---

## 3. Production Deployment Steps (Hostinger VPS)

> **Assumption**: you have SSH access to your Hostinger VPS, with a sudo
> user, and a domain pointing to its IP.

### 3.1 Prepare the VPS (first deploy only)

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install python3.10-venv python3.10-dev build-essential \
                    nginx redis-server certbot python3-certbot-nginx \
                    git ufw

# Optional, for the later PostgreSQL migration:
sudo apt -y install postgresql postgresql-contrib libpq-dev

# Lock down the firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

Create the deploy user and tree:

```bash
sudo adduser --system --group --shell /bin/bash marzouki
sudo mkdir -p /srv/marzouki /srv/backups
sudo chown -R marzouki:marzouki /srv/marzouki /srv/backups
```

### 3.2 Upload the hardened code

Pick one method:

**Option A — git (recommended):**

```bash
sudo -u marzouki bash
cd /srv/marzouki
git clone https://github.com/YOUR_ORG/marzouki.git .
git checkout main   # or your release tag
```

**Option B — SFTP:**

Upload the entire project tree (excluding `venv/`, `__pycache__/`,
`db.sqlite3`, `media/`, `staticfiles/`, `logs/`, `.env`) to
`/srv/marzouki/`.

Make sure ownership is `marzouki:marzouki` and that **none of the
following are present** on the server:
- `.env` in git (it must come from your secrets manager, not the repo)
- `db.sqlite3` from your dev laptop (the server keeps its own DB)
- `media/` from your laptop (the server keeps its own uploads)

### 3.3 Build the venv & install deps

```bash
sudo -u marzouki bash
cd /srv/marzouki
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 Create `.env` from the template

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

**Mandatory values for first deploy:**

```
DJANGO_SECRET_KEY=<run: python -c "import secrets;print(secrets.token_urlsafe(64))">
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=marzoukiart.com,www.marzoukiart.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://marzoukiart.com,https://www.marzoukiart.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=60      # bump to 31536000 once stable

# Leave blank for first deploy (keeps SQLite). Fill once you migrate to PG.
DATABASE_URL=

REDIS_URL=redis://127.0.0.1:6379/1

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<your gmail>
EMAIL_HOST_PASSWORD=<app password>

STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=             # filled after step 3.7
```

### 3.5 Migrate & collect static

```bash
source venv/bin/activate
python manage.py migrate --no-input
python manage.py collectstatic --no-input
python manage.py check --deploy
```

The last command should report **no warnings** about insecure settings if
your `.env` is filled correctly.

### 3.6 Install systemd unit & start Gunicorn

```bash
sudo cp deploy/marzouki.service /etc/systemd/system/marzouki.service
sudo systemctl daemon-reload
sudo systemctl enable --now marzouki
sudo systemctl status marzouki        # confirm "active (running)"
```

Logs:

```bash
sudo journalctl -u marzouki -f
tail -f /srv/marzouki/logs/app.log
```

### 3.7 Configure Nginx + SSL

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/marzouki
sudo ln -sf /etc/nginx/sites-available/marzouki /etc/nginx/sites-enabled/marzouki

# Edit the file: set server_name + paths for your domain
sudo nano /etc/nginx/sites-available/marzouki

# Test syntax and reload
sudo nginx -t && sudo systemctl reload nginx

# Provision Let's Encrypt cert
sudo certbot --nginx -d marzoukiart.com -d www.marzoukiart.com
```

### 3.8 Set up the Stripe webhook

In the Stripe Dashboard:
1. **Developers → Webhooks → Add endpoint**
2. Endpoint URL: `https://marzoukiart.com/stripe/webhook/`
3. Events: at minimum, `checkout.session.completed` (and
   `checkout.session.async_payment_succeeded` if you accept delayed
   payment methods).
4. Copy the **Signing secret** (`whsec_...`) and put it in `.env` as
   `STRIPE_WEBHOOK_SECRET`.
5. Restart Gunicorn:

   ```bash
   sudo systemctl restart marzouki
   ```

6. Run **Send test event** from the Stripe dashboard. The Django log
   should show `payment.webhook: received event checkout.session.completed`.

### 3.9 (Optional but recommended) Sentry

```bash
pip install "sentry-sdk[django]==2.18.0"
# Then add SENTRY_DSN=https://... to .env and the following two lines
# to TheProject/settings.py just below the LOGGING block:
#
#   if os.environ.get("SENTRY_DSN"):
#       import sentry_sdk
#       sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], traces_sample_rate=0.1)
```

---

## 4. Database Migration Instructions (SQLite → PostgreSQL)

PostgreSQL migration is **not required immediately** — the new build runs
fine on the existing SQLite file. Migrate when you have a quiet hour and
have completed the hardening rollout.

### 4.1 Safest path: `dumpdata` / `loaddata`

```bash
# 1. Backup first (see section 1).
# 2. From the running SQLite-backed app:
source venv/bin/activate
python manage.py dumpdata \
    --natural-foreign --natural-primary \
    --exclude contenttypes --exclude auth.permission \
    --indent 2 \
    > /srv/backups/dumpdata-$(date +%F-%H%M).json

# 3. Provision PostgreSQL:
sudo -u postgres psql -c "CREATE USER marzouki WITH PASSWORD '<strong-pw>';"
sudo -u postgres psql -c "CREATE DATABASE marzouki OWNER marzouki;"

# 4. Point .env at PostgreSQL:
#    DATABASE_URL=postgres://marzouki:<strong-pw>@127.0.0.1:5432/marzouki

# 5. Migrate the fresh DB & load data:
python manage.py migrate --no-input
python manage.py loaddata /srv/backups/dumpdata-<timestamp>.json

# 6. Restart and verify:
sudo systemctl restart marzouki
```

If `loaddata` fails because of legacy data quirks (rare but possible on
old databases), you can prune problematic rows from the dump JSON or fall
back to the rollback path in section 1.4.

### 4.2 Rollback to SQLite

```bash
# 1. Set DATABASE_URL= (empty) in /srv/marzouki/.env
# 2. sudo systemctl restart marzouki
```

The app falls back to `db.sqlite3` automatically.

---

## 5. Hostinger-Specific Notes

* **Plan tier.** Use Hostinger **VPS** (Cloud or Business). Shared
  Hosting cannot run Gunicorn/systemd.
* **DNS.** Hostinger's DNS panel: create an A record pointing
  `marzoukiart.com` and `www.marzoukiart.com` at the VPS IP. Wait for
  propagation before running Certbot.
* **Firewall.** Hostinger's VPS firewall (hPanel → Security) may need to
  open ports 80 and 443 in addition to UFW.
* **Time.** Hostinger VPS images sometimes ship with the wrong timezone.
  `sudo timedatectl set-timezone UTC` and let Django convert (`USE_TZ=True`
  is set, and the project's `TIME_ZONE` defaults to `Asia/Qatar`).
* **Email.** Gmail SMTP works fine if you create a Google **App
  Password**. Hostinger SMTP also works — replace `EMAIL_HOST` /
  `EMAIL_HOST_USER` accordingly.
* **Resource limits.** On the entry-level VPS plan, lower
  `GUNICORN_WORKERS` to 2 in `/srv/marzouki/.env` to avoid OOM kills.

---

## 6. Final Verification Checklist

Tick every item before considering the deploy done.

### Security

- [ ] Visiting `/admin/` over HTTP redirects to HTTPS.
- [ ] `https://<domain>/dashboard/admin_home/` redirects anonymous users
      to `/login/`.
- [ ] An authenticated non-staff user visiting `/dashboard/...` does
      **not** see the dashboard.
- [ ] `python manage.py check --deploy` shows **no warnings**.
- [ ] The HTTP response includes `Strict-Transport-Security` (after you
      enable HSTS in `.env`).
- [ ] `/.env` and `/db.sqlite3` are **not** reachable over HTTPS (Nginx
      returns 404).
- [ ] Stripe API keys in `.env` are **live keys**, not test keys (verify
      with `stripe events list --api-key ...`).

### Payments

- [ ] A real test purchase made with `4242 4242 4242 4242` (in test mode)
      shows the order as **paid** in the dashboard.
- [ ] The Django log shows `payment.webhook: order #N marked paid`.
- [ ] Re-sending the same webhook from the Stripe dashboard does **not**
      duplicate the paid flag (idempotency).
- [ ] The success page no longer flips `paid=True` on its own (verifiable
      by deleting the Stripe webhook temporarily — `paid` should remain
      `False` until you re-enable it).

### Catalog & UX

- [ ] `/paints/`, `/originals/`, `/prints/`, `/category/<id>/` all
      paginate properly (the page numbers update, no dead `#` links).
- [ ] Product cards on `/originals/` and `/prints/` show the discounted
      price in green when a discount is active.
- [ ] The cart calculates totals correctly across multiple items with
      variations.

### Operations

- [ ] `sudo systemctl status marzouki` shows **active (running)**.
- [ ] `redis-cli ping` returns `PONG`.
- [ ] `tail -f /srv/marzouki/logs/app.log` shows a steady heartbeat of
      requests (no `Traceback`).
- [ ] Static files load with cache-busted hashed names
      (e.g. `/static/css/main.<hash>.css`).
- [ ] Media uploads (uploading a new product image from the dashboard)
      end up in `/srv/marzouki/media/items_media/`.

### Backups

- [ ] A cron entry exists for `sqlite3 db.sqlite3 ".backup '...'"` or
      `pg_dump` (`crontab -e -u marzouki`).
- [ ] Tested the rollback procedure (section 1.4) on a staging clone.

---

## 7. Cron jobs to add

```cron
# Edit: sudo crontab -e -u marzouki

# Daily SQLite/Postgres backup at 03:00
0 3 * * * /srv/marzouki/deploy/backup.sh

# Weekly old-backup cleanup
0 4 * * 0 find /srv/backups -mtime +30 -delete
```

A sample `backup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%F-%H%M)
mkdir -p /srv/backups

if [[ -n "${DATABASE_URL:-}" ]]; then
    pg_dump -Fc "$DATABASE_URL" > "/srv/backups/db-$TS.dump"
else
    sqlite3 /srv/marzouki/db.sqlite3 ".backup '/srv/backups/db-$TS.sqlite3'"
fi
tar -czf "/srv/backups/media-$TS.tgz" -C /srv/marzouki media
```

---

## 8. Known follow-ups (not blockers)

These were identified during the audit but kept out of this rollout to
avoid scope creep / risk:

* **Self-host Bootstrap & Font Awesome.** Currently still loaded from
  CDN in `base.html`. Move to `staticfiles/css/vendor/` for offline
  resilience.
* **Drop the unused legacy `Cart` DB model** in `TheApp/models.py`. Will
  require an empty migration; deferred so this rollout stays additive.
* **Convert width/height** on `StoreItems` from `FloatField` to
  `DecimalField` (they're physical dimensions, but tiny precision impact).
* **Self-host catalog images via WebP variants.** Plug in a `django-imagekit`
  or `sorl-thumbnail` integration to auto-generate thumbnails.
* **django-axes** for login brute-force protection. Trivial to add — pin
  `django-axes==6.1.1`, add to `INSTALLED_APPS`, and add its middleware.

---

## 9. Summary of files added or rewritten in this rollout

```
.gitignore                                    NEW
.env.example                                  NEW
requirements.txt                              NEW
Procfile                                      REWRITTEN
DEPLOYMENT.md                                 NEW
deploy/gunicorn.conf.py                       NEW
deploy/marzouki.service                       NEW
deploy/nginx.conf.example                     NEW
TheProject/settings.py                        REWRITTEN
TheProject/urls.py                            REWRITTEN
TheProject/build.sh                           REWRITTEN
TheApp/context_processors.py                  NEW
TheApp/validators.py                          NEW
TheApp/forms.py                               REWRITTEN
TheApp/Templates/base.html                    REWRITTEN
TheApp/Templates/error.html                   REWRITTEN
TheApp/Templates/completed.html               REWRITTEN
TheApp/templates/originals.html               EDITED  (pagination)
TheApp/templates/prints.html                  EDITED  (pagination)
TheApp/templates/category_page.html           EDITED  (pagination)
TheApp/templates/partials/_pagination.html    NEW
TheApp/migrations/0089_pricing_indexes_and_validators.py  NEW
cart/cart.py                                  REWRITTEN
cart/pricing.py                               NEW
payment/views.py                              REWRITTEN
payment/urls.py                               REWRITTEN
payment/webhooks.py                           NEW
orders/services/__init__.py                   NEW
orders/services/pricing.py                    NEW
orders/migrations/0020_paid_at_snapshots_indexes.py  NEW
dashboard/decorators.py                       NEW
dashboard/urls.py                             REWRITTEN
.github/workflows/django.yml                  REWRITTEN
```

Everything else (`TheApp/views.py`, `TheApp/models.py`, `orders/views.py`,
`orders/models.py`, `dashboard/views.py`, `dashboard/forms.py`,
`cart/views.py`, `cart/forms.py`) was already refactored prior to this
rollout — those files are referenced from the new code but were not
re-rewritten here.
