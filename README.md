# CVAdapt 🤖

AI-powered CV adaptation SaaS — upload your base CV, paste a job description, and receive a fully rewritten CV, cover letter, and keyword gap analysis in seconds.

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 + Django REST Framework |
| Frontend | Django Templates + TailwindCSS (CDN) + HTMX + Alpine.js |
| AI | OpenAI GPT-4o-mini (or Anthropic Claude) |
| Payments | Stripe Subscriptions (USD) |
| Auth | django-allauth + Google OAuth |
| DB (dev) | SQLite |
| DB (prod) | PostgreSQL via `DATABASE_URL` |
| Hosting | Railway.app / Render.com |

## Project structure

```
cv-adapter/
├── cvadapt/                  # Django project
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py            # SQLite, DEBUG=True
│   │   └── prod.py           # PostgreSQL, HTTPS
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/             # User + Subscription models, allauth signals
│   ├── core/                 # Home, Pricing, middleware, context processor
│   ├── cv_adapter/           # CVBase, JobApplication, AI service, parsers
│   ├── dashboard/            # Dashboard index view
│   └── payments/             # Stripe Checkout + Webhook
├── templates/
│   ├── base.html
│   ├── account/              # allauth login/signup/logout
│   ├── accounts/             # profile
│   ├── core/                 # home, pricing
│   ├── cv_adapter/           # upload, adapt, result, history + partials
│   ├── dashboard/
│   └── payments/             # upgrade, success
├── requirements.txt
├── Procfile
├── railway.toml
└── .env.example
```

## Quick start (local dev)

```bash
# 1. Clone & enter
git clone <repo-url>
cd cv-adapter

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# → Edit .env: set OPENAI_API_KEY, Stripe keys, etc.

# 5. Run migrations
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Start dev server
python manage.py runserver
```

Open http://127.0.0.1:8000

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Django secret key |
| `DEBUG` | ✅ | `True` for dev, `False` for prod |
| `ALLOWED_HOSTS` | ✅ prod | Comma-separated hostnames |
| `DATABASE_URL` | ✅ prod | PostgreSQL connection string |
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `AI_PROVIDER` | — | `openai` (default) or `anthropic` |
| `AI_MODEL` | — | `gpt-4o-mini` (default) |
| `ANTHROPIC_API_KEY` | if using Claude | Anthropic API key |
| `STRIPE_PUBLISHABLE_KEY` | ✅ | Stripe publishable key |
| `STRIPE_SECRET_KEY` | ✅ | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Stripe webhook signing secret |
| `STRIPE_PRO_PRICE_ID` | ✅ | Stripe recurring price ID for Pro plan |
| `GOOGLE_CLIENT_ID` | optional | For Google OAuth login |
| `GOOGLE_CLIENT_SECRET` | optional | For Google OAuth login |

## Stripe setup

1. Create a product "CVAdapt Pro" in the Stripe dashboard.
2. Add a recurring price of **$9.90 / month (USD)** and copy the Price ID → `STRIPE_PRO_PRICE_ID`.
3. For local webhook testing use [Stripe CLI](https://stripe.com/docs/stripe-cli):
   ```bash
   stripe listen --forward-to localhost:8000/payments/webhook/
   ```
4. Copy the webhook signing secret → `STRIPE_WEBHOOK_SECRET`.

## Plans

| Plan | Adaptations/month | Price |
|---|---|---|
| Free | 3 | $0 |
| Pro | Unlimited | $9.90/mo |

## Deploy to Railway

1. Push to GitHub.
2. New project → Deploy from GitHub repo.
3. Add PostgreSQL plugin (free tier).
4. Set all environment variables listed above with production values.
5. Railway auto-detects `railway.toml` and runs migrations + gunicorn.

## AI prompt

The system sends the extracted CV text + full JD to GPT-4o-mini and requests this structured JSON:

```json
{
  "cv_adaptado":           "full rewritten CV text",
  "cover_letter":          "full cover letter text",
  "keywords_encontradas":  ["Python", "Django", ...],
  "keywords_faltando":     ["Kubernetes", "AWS", ...],
  "sugestoes":             ["Add quantified achievements to experience section", ...],
  "score":                 82
}
```

## License

MIT
