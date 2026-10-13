# Digital Literacy in Rural and Semi-Urban Areas

A Flask college project with registration/login, learning resources, a 10-question quiz, saved quiz results, feedback, and an admin dashboard.

## Deploy online using Render

1. Extract this ZIP on your computer.
2. Create a GitHub account (if you do not already have one) and create a **new private repository** named `digital-literacy-project`.
3. Upload the extracted project files to that repository. Keep `render.yaml` in the repository root.
4. Sign in to Render and choose **New + → Blueprint**. Connect the GitHub repository and follow the prompts.
5. When asked for `ADMIN_PASSWORD`, enter a strong password. Do not use `admin123` for a public deployment.
6. Deploy. Render will provide a public `onrender.com` URL when deployment finishes.

**Hosting cost note:** this configuration uses a persistent disk so registrations, quiz results, and feedback survive restarts/redeploys. Render persistent disks may require a paid plan; check current pricing before confirming. Do not remove the disk or change `DB_PATH` unless you have migrated the database, or existing records may no longer be available.

## Run locally in VS Code

1. Install Python 3.11+.
2. Open this folder in VS Code and open Terminal.
3. Run `python -m venv venv`.
4. Windows: `venv\Scripts\activate` (macOS/Linux: `source venv/bin/activate`).
5. Run `pip install -r requirements.txt`.
6. Run `python app.py` and open `http://127.0.0.1:5000`.

## Admin page

Admin URL: `/admin/login` (locally: `http://127.0.0.1:5000/admin/login`).

Locally, the demo credentials are username `admin`, password `admin123`. Online, set `ADMIN_PASSWORD` in Render to a strong unique password. You can set `ADMIN_USERNAME` there too.

## Database and security

SQLite is used. `DB_PATH` determines the database location; Render's persistent disk is mounted at `/var/data` in this configuration. The app reads `SECRET_KEY` from the environment. Never publish real user data, passwords, or secret values in a public GitHub repository. Passwords are stored as hashes.
