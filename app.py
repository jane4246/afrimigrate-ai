from flask import Flask, render_template, request, jsonify
from datetime import datetime
import sqlite3
import os
import io
import base64
import qrcode

app = Flask(__name__)

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "afrimigrate.db"
)


# ============================================================
# SYNTHETIC DEMONSTRATION KNOWLEDGE BASE
# ============================================================

DEMO_RULES = [
    {
        "country": "Kenya",
        "nationality": "Uganda",
        "purpose": "Employment",
        "answer": (
            "For this demonstration journey, prepare a valid travel document, "
            "employment documentation, and any applicable authorization or permit "
            "documentation. The prototype does not determine legal eligibility; "
            "confirm current requirements with the relevant official authority."
        ),
        "source": "AfriMigrate Demonstration Migration Rules Database",
        "updated": "September 2026",
        "confidence": "High",
        "human": (
            "Yes — confirm current legal requirements with an authorized authority."
        )
    },

    {
        "country": "Kenya",
        "nationality": "Any",
        "purpose": "General",
        "answer": (
            "Migration requirements can depend on nationality, purpose and duration "
            "of stay. Use the readiness checker for a demonstration checklist, "
            "then verify current requirements through the relevant official authority."
        ),
        "source": "AfriMigrate Demonstration Migration Rules Database",
        "updated": "September 2026",
        "confidence": "High",
        "human": "Yes — official confirmation is recommended."
    }
]


# ============================================================
# SYNTHETIC DIGITAL CREDENTIALS
# ============================================================

DEMO_CREDENTIALS = {

    "AFM-KE-2026-000184": {
        "status": "Valid",
        "country": "Kenya",
        "purpose": "Employment",
        "valid_until": "15 March 2027",
        "issuer": "Authorized Demo Authority",
        "identity": "Verified"
    },

    "AFM-UG-2026-000072": {
        "status": "Pending Review",
        "country": "Uganda",
        "purpose": "Study",
        "valid_until": "20 January 2027",
        "issuer": "Authorized Demo Authority",
        "identity": "Verification pending"
    }
}


# ============================================================
# DATABASE
# ============================================================

def init_db():

    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True
    )

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            country TEXT,

            purpose TEXT,

            issue TEXT,

            month TEXT
        )
    """)

    cur.execute(
        "SELECT COUNT(*) FROM applications"
    )

    if cur.fetchone()[0] == 0:

        seed = [

            (
                "Kenya",
                "Employment",
                "Employment documentation",
                "Sep 2026"
            ),

            (
                "Kenya",
                "Employment",
                "Employment documentation",
                "Sep 2026"
            ),

            (
                "Kenya",
                "Study",
                "Passport/document issue",
                "Sep 2026"
            ),

            (
                "Uganda",
                "Employment",
                "Missing supporting document",
                "Sep 2026"
            ),

            (
                "Tanzania",
                "Employment",
                "Incomplete application",
                "Sep 2026"
            ),

            (
                "Rwanda",
                "Study",
                "Passport/document issue",
                "Sep 2026"
            ),

            (
                "Kenya",
                "Employment",
                "Employment documentation",
                "Sep 2026"
            ),

            (
                "Uganda",
                "Study",
                "Other",
                "Sep 2026"
            ),

            (
                "Tanzania",
                "Employment",
                "Employment documentation",
                "Sep 2026"
            ),

            (
                "Rwanda",
                "Employment",
                "Missing supporting document",
                "Sep 2026"
            )
        ]

        cur.executemany(
            """
            INSERT INTO applications
            (country, purpose, issue, month)

            VALUES (?, ?, ?, ?)
            """,
            seed
        )

    conn.commit()

    conn.close()


# ============================================================
# QR CODE
# ============================================================

def credential_qr_data_url(credential_id):

    payload = (
        f"{request.host_url.rstrip('/')}"
        f"/verify?credential={credential_id}"
    )

    img = qrcode.make(payload)

    buffer = io.BytesIO()

    img.save(
        buffer,
        format="PNG"
    )

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode()

    return (
        "data:image/png;base64,"
        + encoded
    )


# ============================================================
# MAIN PAGES
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


@app.route("/assistant")
def assistant():

    return render_template(
        "assistant.html"
    )


@app.route("/readiness")
def readiness():

    return render_template(
        "readiness.html"
    )


@app.route("/credential")
def credential():

    credential_id = request.args.get(
        "id",
        "AFM-KE-2026-000184"
    )

    credential = DEMO_CREDENTIALS.get(
        credential_id
    )

    if not credential:

        credential_id = (
            "AFM-KE-2026-000184"
        )

        credential = DEMO_CREDENTIALS[
            credential_id
        ]

    qr = credential_qr_data_url(
        credential_id
    )

    return render_template(
        "credential.html",

        credential_id=credential_id,

        credential=credential,

        qr=qr
    )


@app.route("/verify")
def verify():

    credential_id = request.args.get(
        "credential",
        ""
    ).strip()

    credential = DEMO_CREDENTIALS.get(
        credential_id
    )

    return render_template(
        "verify.html",

        credential_id=credential_id,

        credential=credential
    )


@app.route("/officer")
def officer():

    return render_template(
        "officer.html"
    )


@app.route("/policy")
def policy():

    conn = sqlite3.connect(
        DB_PATH
    )

    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM applications"
    )

    total = cur.fetchone()[0]

    cur.execute("""
        SELECT
            issue,
            COUNT(*)

        FROM applications

        GROUP BY issue

        ORDER BY COUNT(*) DESC
    """)

    issues = cur.fetchall()

    cur.execute("""
        SELECT
            country,
            COUNT(*)

        FROM applications

        GROUP BY country

        ORDER BY COUNT(*) DESC
    """)

    countries = cur.fetchall()

    conn.close()

    return render_template(
        "policy.html",

        total=total,

        issues=issues,

        countries=countries
    )


@app.route("/interoperability")
def interoperability():

    return render_template(
        "interoperability.html"
    )


@app.route("/privacy")
def privacy():

    return render_template(
        "privacy.html"
    )


# ============================================================
# AI ASSISTANT API
# ============================================================

@app.route(
    "/api/assistant",
    methods=["POST"]
)
def api_assistant():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    nationality = data.get(
        "nationality",
        "Any"
    )

    destination = data.get(
        "destination",
        "Kenya"
    )

    purpose = data.get(
        "purpose",
        "General"
    )

    question = data.get(
        "question",
        ""
    ).strip()


    rule = next(

        (
            r
            for r in DEMO_RULES

            if (
                r["country"].lower()
                == destination.lower()
            )

            and (

                r["nationality"].lower()
                == nationality.lower()

                or

                r["nationality"]
                == "Any"
            )

            and (

                r["purpose"].lower()
                == purpose.lower()

                or

                r["purpose"]
                == "General"
            )
        ),

        DEMO_RULES[1]
    )


    if question:

        answer = rule["answer"]

    else:

        answer = (
            f"For the demonstration profile "
            f"({nationality} → {destination}, {purpose}), "
            f"{rule['answer']}"
        )


    return jsonify({

        "answer": answer,

        "source": rule["source"],

        "updated": rule["updated"],

        "confidence": rule["confidence"],

        "human": rule["human"]

    })


# ============================================================
# DOCUMENT READINESS API
# ============================================================

@app.route(
    "/api/readiness",
    methods=["POST"]
)
def api_readiness():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    passport = bool(
        data.get("passport")
    )

    employment = bool(
        data.get("employment")
    )

    supporting = bool(
        data.get("supporting")
    )


    items = [

        {
            "name":
                "Travel document / passport",

            "status":
                "Provided"
                if passport
                else "Missing",

            "ok":
                passport
        },

        {
            "name":
                "Employment documentation",

            "status":
                "Provided"
                if employment
                else "Missing",

            "ok":
                employment
        },

        {
            "name":
                "Applicable authorization / permit",

            "status":
                "Review required",

            "ok":
                False
        },

        {
            "name":
                "Supporting documentation",

            "status":
                "Provided"
                if supporting
                else "Missing",

            "ok":
                supporting
        }
    ]


    return jsonify({

        "items": items,

        "message":
            "This is a demonstration readiness "
            "assessment, not a legal eligibility decision."

    })


# ============================================================
# CREDENTIAL VERIFICATION API
# ============================================================

@app.route(
    "/api/verify",
    methods=["POST"]
)
def api_verify():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    credential_id = data.get(
        "credential_id",
        ""
    ).strip()


    credential = DEMO_CREDENTIALS.get(
        credential_id
    )


    if not credential:

        return jsonify({

            "found": False,

            "message":
                "Credential not found in the "
                "synthetic demonstration registry."

        })


    return jsonify({

        "found": True,

        "credential_id":
            credential_id,

        **credential

    })


# ============================================================
# GLOBAL VARIABLES
# ============================================================

@app.context_processor
def inject_globals():

    return {

        "year":
            datetime.now().year

    }


# ============================================================
# START DATABASE
# ============================================================

init_db()


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=True
    )