import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Local development only. In production, gunicorn serves wsgi:app instead
    # (see wsgi.py / render.yaml), so this dev server never runs there.
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
