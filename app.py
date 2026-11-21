#!/usr/bin/env python3
"""
Drishyam CTF Lab: Dhyan Cable Vision & Rajakkad Archive Portal
A self-contained Flask CTF Web Application featuring:
- Educational CTF authentication challenge (SQLite query logic + OSINT lore discovery)
- Atmospheric Drishyam Malayalam movie theme (serves bg.jpg + built-in Kerala night SVG fallback)
- Home page with storyline welcome message & post-login SSH Key Vault div
"""

import base64
import hashlib
import os
import sqlite3
from pathlib import Path
from flask import (
    Flask,
    Response,
    flash,
    g,
    redirect,
    render_template_string,
    request,
    send_file,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "drishyam_rajakkad_oct_02_lab_session")

DB_PATH = Path(__file__).resolve().parent / "drishyam_ctf.db"
CTF_WEB_FLAG = "CTF{dR1sHy4m_02_0cT_aL1b1_v3r1f13d}"


def generate_sample_ssh_keys():
    """Generate a deterministic, realistic sample RSA key pair for the CTF lab vault."""
    seed_material = b"drishyam-rajakkad-dhyan-cable-vision-october-02-alibi-seed"
    blocks = []
    for i in range(18):
        digest = hashlib.sha512(seed_material + str(i).encode()).digest()
        blocks.append(base64.b64encode(digest).decode("ascii"))
    body_b64 = "".join(blocks)
    wrapped_lines = [body_b64[i : i + 64] for i in range(0, len(body_b64), 64)]

    header = "-----" + "BEGIN OPENSSH" + " SAMPLE KEY" + "-----"
    footer = "-----" + "END OPENSSH" + " SAMPLE KEY" + "-----"
    priv_key = "\n".join([header] + wrapped_lines + [footer])

    pub_b64 = base64.b64encode(hashlib.sha512(seed_material).digest() * 3).decode("ascii")
    pub_key = f"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ{pub_b64[:180]} georgekutty@rajakkad-cable-node"
    return priv_key, pub_key


SSH_PRIVATE_KEY, SSH_PUBLIC_KEY = generate_sample_ssh_keys()


def get_db():
    """Return a SQLite connection for the current request context."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(str(DB_PATH))
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize and seed the SQLite database with Drishyam storyline accounts."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            clearance_note TEXT NOT NULL
        )
        """
    )
    cursor.execute("DELETE FROM users")
    users_seed = [
        (
            "georgekutty",
            "02Oct_SwamiRetreat!",
            "Georgekutty (Dhyan Cable Vision)",
            "Proprietor & Node Administrator",
            "Verified Alibi: Attended Swami Chinmayananda Satsang in Thodupuzha on Oct 2 & Oct 3. Stayed at Bismi Lodge, watched a cinema, and dined at Hotel Jaya.",
        ),
        (
            "geetha_ig",
            "Rajakkad_CaseFile#13",
            "Geetha Prabhakar IPS",
            "Inspector General",
            "Special Investigation Access — High-Range District Archive.",
        ),
        (
            "rani",
            "Family_Alibi_Oct02",
            "Rani George",
            "Archive Co-Custodian",
            "Thodupuzha Trip Receipt Verification Access.",
        ),
    ]
    cursor.executemany(
        "INSERT INTO users (username, password, full_name, role, clearance_note) VALUES (?, ?, ?, ?, ?)",
        users_seed,
    )
    conn.commit()
    conn.close()


BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dhyan Cable Vision | Rajakkad Node & Alibi Archive</title>
    <style>
        :root {
            --bg-deep: #060d0b;
            --card-bg: rgba(9, 20, 17, 0.82);
            --card-border: rgba(229, 169, 59, 0.34);
            --amber-primary: #e5a93b;
            --amber-glow: rgba(229, 169, 59, 0.25);
            --text-main: #edf2f0;
            --text-muted: #9cb0a8;
            --danger: #ef4444;
            --success: #10b981;
            --mono: "JetBrains Mono", "Fira Code", "Courier New", monospace;
            --sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: var(--sans);
            color: var(--text-main);
            background-color: var(--bg-deep);
            background-image:
                linear-gradient(180deg, rgba(4, 10, 8, 0.65) 0%, rgba(6, 15, 12, 0.82) 60%, rgba(4, 9, 7, 0.94) 100%),
                url('/bg.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            line-height: 1.6;
        }

        body::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                radial-gradient(circle at 72% 22%, rgba(229, 169, 59, 0.12), transparent 45%),
                radial-gradient(circle at 25% 75%, rgba(16, 185, 129, 0.07), transparent 50%);
            z-index: 0;
        }

        header {
            position: relative;
            z-index: 2;
            border-bottom: 1px solid var(--card-border);
            background: rgba(5, 12, 10, 0.86);
            backdrop-filter: blur(12px);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }

        .brand-badge {
            width: 42px;
            height: 42px;
            border-radius: 8px;
            background: linear-gradient(135deg, #e5a93b, #8a5a10);
            display: grid;
            place-items: center;
            font-weight: 800;
            color: #060d0b;
            font-family: var(--mono);
            box-shadow: 0 0 16px var(--amber-glow);
        }

        .brand-text h1 {
            font-size: 1.15rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--amber-primary);
        }

        .brand-text p {
            font-size: 0.78rem;
            color: var(--text-muted);
            font-family: var(--mono);
        }

        nav {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }

        .nav-link {
            color: var(--text-main);
            text-decoration: none;
            font-size: 0.9rem;
            padding: 0.45rem 0.95rem;
            border-radius: 6px;
            border: 1px solid transparent;
            transition: all 0.2s ease;
        }

        .nav-link:hover {
            border-color: var(--card-border);
            background: rgba(229, 169, 59, 0.12);
            color: var(--amber-primary);
        }

        .nav-btn {
            background: var(--amber-primary);
            color: #060d0b;
            font-weight: 600;
        }

        .nav-btn:hover {
            background: #f3bc56;
            color: #060d0b;
        }

        main {
            position: relative;
            z-index: 2;
            flex: 1;
            max-width: 1060px;
            width: 100%;
            margin: 2.2rem auto;
            padding: 0 1.5rem;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 2rem;
            backdrop-filter: blur(14px);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.65);
            margin-bottom: 1.75rem;
        }

        .tag-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-family: var(--mono);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--amber-primary);
            background: rgba(229, 169, 59, 0.12);
            border: 1px solid rgba(229, 169, 59, 0.35);
            padding: 0.28rem 0.75rem;
            border-radius: 999px;
            margin-bottom: 1rem;
        }

        .hero-title {
            font-size: 1.95rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: #ffffff;
            line-height: 1.25;
        }

        .story-quote {
            border-left: 3px solid var(--amber-primary);
            padding: 0.85rem 1.25rem;
            margin: 1.25rem 0;
            background: rgba(229, 169, 59, 0.08);
            border-radius: 0 8px 8px 0;
            font-style: italic;
            color: #dce7e3;
        }

        .evidence-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(215px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }

        .evidence-item {
            background: rgba(5, 13, 11, 0.78);
            border: 1px solid rgba(156, 176, 168, 0.2);
            border-radius: 8px;
            padding: 1rem;
        }

        .evidence-item .label {
            font-family: var(--mono);
            font-size: 0.72rem;
            color: var(--amber-primary);
            text-transform: uppercase;
        }

        .evidence-item .value {
            font-size: 0.95rem;
            font-weight: 600;
            margin-top: 0.25rem;
        }

        /* Post-login SSH Keys Div */
        #ssh-keys-div {
            border: 1px solid rgba(16, 185, 129, 0.45);
            background: linear-gradient(165deg, rgba(8, 25, 20, 0.92), rgba(5, 14, 12, 0.96));
        }

        .vault-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1.25rem;
            border-bottom: 1px solid rgba(16, 185, 129, 0.22);
            padding-bottom: 1rem;
        }

        .flag-banner {
            background: rgba(16, 185, 129, 0.12);
            border: 1px dashed var(--success);
            color: #6ee7b7;
            padding: 0.65rem 1rem;
            border-radius: 8px;
            font-family: var(--mono);
            font-size: 0.88rem;
            margin-bottom: 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .key-box-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: var(--mono);
            font-size: 0.8rem;
            color: var(--amber-primary);
            margin: 1rem 0 0.4rem 0;
        }

        pre.ssh-key-block {
            background: #030806;
            border: 1px solid rgba(229, 169, 59, 0.28);
            border-radius: 8px;
            padding: 1rem;
            font-family: var(--mono);
            font-size: 0.78rem;
            color: #a7f3d0;
            overflow-x: auto;
            white-space: pre;
            line-height: 1.45;
            max-height: 280px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.6rem 1.15rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid transparent;
            text-decoration: none;
            transition: all 0.2s ease;
        }

        .btn-amber {
            background: var(--amber-primary);
            color: #060d0b;
        }

        .btn-amber:hover {
            background: #f4be59;
        }

        .btn-outline {
            background: rgba(229, 169, 59, 0.1);
            border-color: var(--card-border);
            color: var(--amber-primary);
        }

        .btn-outline:hover {
            background: rgba(229, 169, 59, 0.22);
        }

        .login-wrapper {
            max-width: 460px;
            margin: 1.5rem auto;
        }

        .form-group {
            margin-bottom: 1.2rem;
        }

        .form-group label {
            display: block;
            font-size: 0.85rem;
            font-family: var(--mono);
            color: var(--text-muted);
            margin-bottom: 0.45rem;
        }

        .form-control {
            width: 100%;
            padding: 0.75rem 1rem;
            border-radius: 6px;
            border: 1px solid rgba(156, 176, 168, 0.3);
            background: rgba(4, 10, 8, 0.85);
            color: var(--text-main);
            font-family: var(--mono);
            font-size: 0.92rem;
        }

        .form-control:focus {
            outline: none;
            border-color: var(--amber-primary);
            box-shadow: 0 0 0 3px var(--amber-glow);
        }

        .alert {
            padding: 0.85rem 1rem;
            border-radius: 8px;
            margin-bottom: 1.25rem;
            font-size: 0.88rem;
            font-family: var(--mono);
        }

        .alert-error {
            background: rgba(239, 68, 68, 0.14);
            border: 1px solid rgba(239, 68, 68, 0.45);
            color: #fca5a5;
        }

        .alert-success {
            background: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(16, 185, 129, 0.45);
            color: #6ee7b7;
        }

        footer {
            position: relative;
            z-index: 2;
            text-align: center;
            padding: 1.25rem;
            font-size: 0.78rem;
            color: var(--text-muted);
            font-family: var(--mono);
            border-top: 1px solid rgba(229, 169, 59, 0.15);
            background: rgba(4, 9, 7, 0.85);
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="brand-badge">DCV</div>
            <div class="brand-text">
                <h1>Dhyan Cable Vision</h1>
                <p>Rajakkad High-Range Node • Idukki District</p>
            </div>
        </div>
        <nav>
            <a href="{{ url_for('home') }}" class="nav-link">Home</a>
            {% if session.get('user') %}
                <a href="#ssh-keys-div" class="nav-link">SSH Keys</a>
                <a href="{{ url_for('logout') }}" class="nav-link nav-btn">Logout ({{ session['user']['username'] }})</a>
            {% else %}
                <a href="{{ url_for('login') }}" class="nav-link nav-btn">Operator Login</a>
            {% endif %}
        </nav>
    </header>

    <main>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, msg in messages %}
                    <div class="alert alert-{{ category }}">{{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {{ content | safe }}
    </main>

    <footer>
        Dhyan Cable Vision Archive System v2.10.2 • "Every visual leaves a trace, but the October 2nd alibi holds."
        <!-- CTF Lab Note: Legacy query builder active on /login. Check /robots.txt for operator alibi notes. -->
    </footer>

    <script>
        function copyBlock(elementId, btnEl) {
            const text = document.getElementById(elementId).innerText;
            navigator.clipboard.writeText(text).then(() => {
                const prev = btnEl.innerText;
                btnEl.innerText = "Copied!";
                setTimeout(() => btnEl.innerText = prev, 1800);
            });
        }
    </script>
</body>
</html>
"""

HOME_CONTENT = """
<div class="card">
    <span class="tag-pill">● Rajakkad Node Status: Online • Case File #02-OCT</span>
    <h2 class="hero-title">Welcome to the Dhyan Cable Vision & Alibi Archive</h2>
    <p>
        {% if session.get('user') %}
            Welcome back, <strong>{{ session['user']['full_name'] }}</strong>
            (<em>{{ session['user']['role'] }}</em>). Your session is verified against the
            Rajakkad High-Range Node. The post-login SSH keys for the cable office relay server
            are displayed in the vault panel below.
        {% else %}
            Welcome to the internal transmission and surveillance portal of <strong>Dhyan Cable Vision, Rajakkad</strong>.
            Only authenticated cable operators and cleared officers with October 2nd verification may view the
            relay server SSH credentials.
        {% endif %}
    </p>

    <blockquote class="story-quote">
        "Remember every detail: On October 2nd and 3rd, we travelled to Thodupuzha for Swami Chinmayananda's satsang,
        stayed at Bismi Lodge, watched a movie at the cinema hall, and had meals at Hotel Jaya. The receipts are kept
        safely in the cable office drawer."
    </blockquote>

    <div class="evidence-grid">
        <div class="evidence-item">
            <div class="label">Alibi Timeline</div>
            <div class="value">02 Oct – 03 Oct (Thodupuzha)</div>
        </div>
        <div class="evidence-item">
            <div class="label">Verified Receipts</div>
            <div class="value">Bismi Lodge & Hotel Jaya</div>
        </div>
        <div class="evidence-item">
            <div class="label">Relay Node</div>
            <div class="value">Dhyan Cable Office #04</div>
        </div>
        <div class="evidence-item">
            <div class="label">Vault Clearance</div>
            <div class="value">
                {% if session.get('user') %}
                    <span style="color: #10b981;">● Unlocked ({{ session['user']['username'] }})</span>
                {% else %}
                    <span style="color: #f59e0b;">● Locked — Login Required</span>
                {% endif %}
            </div>
        </div>
    </div>

    {% if not session.get('user') %}
        <div style="margin-top: 1.5rem;">
            <a href="{{ url_for('login') }}" class="btn btn-amber">Proceed to Operator Login →</a>
        </div>
    {% endif %}
</div>

{% if session.get('user') %}
<!-- Dedicated Post-Login Div Displaying SSH Keys -->
<div id="ssh-keys-div" class="card">
    <div class="vault-header">
        <div>
            <span class="tag-pill" style="color: #6ee7b7; border-color: rgba(16,185,129,0.4); background: rgba(16,185,129,0.12);">
                🔓 Post-Login SSH Key Vault
            </span>
            <h3 style="font-size: 1.45rem; color: #ffffff;">Rajakkad Relay Server — SSH Key Pair</h3>
            <p style="font-size: 0.88rem; color: var(--text-muted); margin-top: 0.2rem;">
                {{ session['user']['clearance_note'] }}
            </p>
        </div>
        <div style="display: flex; gap: 0.6rem; flex-wrap: wrap;">
            <button class="btn btn-outline" onclick="copyBlock('ssh-private-key', this)">Copy Private Key</button>
            <a href="{{ url_for('download_ssh_key') }}" class="btn btn-amber">Download id_rsa</a>
        </div>
    </div>

    <div class="flag-banner">
        <span><strong>Stage 1 Flag:</strong> {{ flag }}</span>
        <span><strong>SSH Target:</strong> georgekutty@rajakkad-node (Port 2222)</span>
    </div>

    <div class="key-box-label">
        <span>SSH PRIVATE KEY (id_rsa — 2048-bit Sample Lab Key)</span>
        <span>chmod 600 id_rsa && ssh -i id_rsa georgekutty@&lt;BOX_IP&gt; -p 2222</span>
    </div>
    <pre id="ssh-private-key" class="ssh-key-block">{{ ssh_private_key }}</pre>

    <div class="key-box-label">
        <span>AUTHORIZED PUBLIC KEY (id_rsa.pub)</span>
        <button class="btn btn-outline" style="padding: 0.25rem 0.65rem; font-size: 0.75rem;" onclick="copyBlock('ssh-public-key', this)">Copy Public Key</button>
    </div>
    <pre id="ssh-public-key" class="ssh-key-block" style="color: #fde68a;">{{ ssh_public_key }}</pre>
</div>
{% endif %}
"""

LOGIN_CONTENT = """
<div class="login-wrapper">
    <div class="card">
        <span class="tag-pill">Restricted Terminal #04</span>
        <h2 style="font-size: 1.55rem; margin-bottom: 0.4rem;">Operator Login</h2>
        <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1.5rem;">
            Authenticate with your Dhyan Cable Vision operator credentials to view the SSH Key Vault.
        </p>

        {% if sql_error %}
            <div class="alert alert-error">
                <strong>[SQLite Query Error]:</strong><br>{{ sql_error }}
                <br><br><em>Query:</em><br><code>{{ executed_query }}</code>
            </div>
        {% endif %}

        <form method="POST" action="{{ url_for('login') }}">
            <div class="form-group">
                <label for="username">OPERATOR USERNAME</label>
                <input type="text" id="username" name="username" class="form-control"
                       placeholder="e.g. georgekutty" required autocomplete="off">
            </div>
            <div class="form-group">
                <label for="password">ALIBI PASSKEY</label>
                <input type="password" id="password" name="password" class="form-control"
                       placeholder="Enter passkey..." required>
            </div>
            <button type="submit" class="btn btn-amber" style="width: 100%; justify-content: center; padding: 0.8rem;">
                Sign In & Reveal SSH Keys
            </button>
        </form>
    </div>
</div>
"""


@app.route("/")
def home():
    rendered_home = render_template_string(
        HOME_CONTENT,
        ssh_private_key=SSH_PRIVATE_KEY,
        ssh_public_key=SSH_PUBLIC_KEY,
        flag=CTF_WEB_FLAG,
    )
    return render_template_string(BASE_TEMPLATE, content=rendered_home)


@app.route("/login", methods=["GET", "POST"])
def login():
    sql_error = None
    executed_query = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Intentional CTF challenge mechanism: unparameterized query construction
        executed_query = (
            f"SELECT id, username, full_name, role, clearance_note "
            f"FROM users WHERE username = '{username}' AND password = '{password}'"
        )

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(executed_query)
            user_row = cursor.fetchone()

            if user_row:
                session["user"] = {
                    "id": user_row["id"],
                    "username": user_row["username"],
                    "full_name": user_row["full_name"],
                    "role": user_row["role"],
                    "clearance_note": user_row["clearance_note"],
                }
                flash(f"Login successful. Welcome, {user_row['full_name']}.", "success")
                return redirect(url_for("home"))
            else:
                flash("Access Denied: Invalid operator username or passkey.", "error")
        except sqlite3.Error as err:
            sql_error = str(err)

    rendered_login = render_template_string(
        LOGIN_CONTENT,
        sql_error=sql_error,
        executed_query=executed_query,
    )
    return render_template_string(BASE_TEMPLATE, content=rendered_login)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out. SSH Key Vault locked.", "success")
    return redirect(url_for("home"))


@app.route("/download-key")
def download_ssh_key():
    if not session.get("user"):
        flash("Please log in first to download the SSH key.", "error")
        return redirect(url_for("login"))
    return Response(
        SSH_PRIVATE_KEY + "\n",
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=id_rsa"},
    )


@app.route("/robots.txt")
def robots_txt():
    """CTF Recon Route #1."""
    content = (
        "User-agent: *\n"
        "Disallow: /alibi-notes.txt\n"
        "Disallow: /login\n"
    )
    return Response(content, mimetype="text/plain")


@app.route("/alibi-notes.txt")
def alibi_notes():
    """CTF Recon Route #2 with Drishyam storyline clues."""
    content = (
        "=== DHYAN CABLE VISION — DESK DRAWER MEMO ===\n"
        "Operator: georgekutty\n"
        "Alibi Receipts: Bismi Lodge, Cinema Ticket, Hotel Jaya (02 Oct - 03 Oct)\n"
        "Backup Passkey: 02Oct_SwamiRetreat!\n"
    )
    return Response(content, mimetype="text/plain")


@app.route("/bg.jpg")
def background_image():
    """
    Serve the bundled Drishyam background image if present in the app directory
    (e.g. bg.jpg or drishyam_bg.jpg), or fall back to an embedded SVG Kerala hill-station scene.
    """
    base_dir = Path(__file__).resolve().parent
    for candidate in ("bg.jpg", "drishyam_bg.jpg", "drishyam_bg.png", "background.jpg"):
        candidate_path = base_dir / candidate
        if candidate_path.is_file():
            mime = "image/png" if candidate.endswith(".png") else "image/jpeg"
            return send_file(str(candidate_path), mimetype=mime)

    svg_backdrop = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
        <defs>
            <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#030907"/>
                <stop offset="50%" stop-color="#091914"/>
                <stop offset="100%" stop-color="#050d0a"/>
            </linearGradient>
            <radialGradient id="lamp" cx="72%" cy="54%" r="32%">
                <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.55"/>
                <stop offset="45%" stop-color="#d97706" stop-opacity="0.18"/>
                <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
            </radialGradient>
        </defs>
        <rect width="1920" height="1080" fill="url(#sky)"/>
        <path d="M0 640 Q320 480 680 570 T1360 510 T1920 590 L1920 1080 L0 1080 Z" fill="#07130f"/>
        <circle cx="1382" cy="580" r="520" fill="url(#lamp)"/>
    </svg>"""
    return Response(svg_backdrop, mimetype="image/svg+xml")


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
