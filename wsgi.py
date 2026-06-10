"""
WSGI entrypoint for production servers (gunicorn).

Run in production with:
    gunicorn wsgi:app

Render uses this automatically via render.yaml. FLASK_ENV=production
selects ProductionConfig (debug off, secret key required from the environment).
"""

from app import create_app

app = create_app("production")

if __name__ == "__main__":
    # Local fallback only — gunicorn imports `app` above and does not run this.
    app.run()
