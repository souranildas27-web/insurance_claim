"""
Insurance Claim Management & Risk Review System
------------------------------------------------
Simple Flask demo app (educational purpose).

Workflow: login -> create policy -> submit claim -> auto risk flag
          -> review in claims list -> update status -> track on dashboard.

All data lives in memory (dicts) and resets on restart. No database.
Run with:  python app.py
"""

from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
# Secret key is only used to sign the demo session cookie (not production).
app.secret_key = "dev-secret-key-change-me"

# ---------------------------------------------------------------------------
# Hard-coded credential (per PRD: no real auth system required)
# ---------------------------------------------------------------------------
USERNAME = "admin"
PASSWORD = "admin123"

# ---------------------------------------------------------------------------
# In-memory storage (resets when the process restarts)
# ---------------------------------------------------------------------------
# policy_number -> policy dict
policies = {}
# claim_id -> claim dict
claims = {}
# Counter used when the user leaves Claim ID blank (auto-generation).
claim_counter = 1

STATUS_CHOICES = ["Submitted", "Under Review", "Approved", "Rejected"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def login_required(view_func):
    """Redirect unauthenticated users to the login page."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def generate_claim_id():
    """Generate the next unique Claim ID like CLM-0001, CLM-0002, ..."""
    global claim_counter
    while True:
        candidate = f"CLM-{claim_counter:04d}"
        claim_counter += 1
        if candidate not in claims:
            return candidate


def classify_risk(claim_amount, coverage_amount, policy_exists,
                  previous_claim_count, description):
    """Apply the PRD Section 7 rule set.

    Returns (risk_level, risk_reasons).
    Severity order: High Risk > Review Required > Normal.
    """
    reasons = []
    level = "Normal"

    # Rule 1 & 2: claim size relative to the linked policy's coverage.
    # Only applies when we know the policy and its coverage.
    if policy_exists and coverage_amount is not None:
        if claim_amount > 0.8 * coverage_amount:
            level = "High Risk"
            reasons.append(
                f"Claim amount ({claim_amount:g}) exceeds 80% of "
                f"policy coverage ({coverage_amount:g})."
            )
        elif claim_amount > 0.5 * coverage_amount:
            level = "Review Required"
            reasons.append(
                f"Claim amount ({claim_amount:g}) exceeds 50% of "
                f"policy coverage ({coverage_amount:g})."
            )

    # Rule 3: unknown / unlinked policy number.
    if not policy_exists:
        if level != "High Risk":
            level = "Review Required"
        reasons.append("Policy number does not match any recorded policy.")

    # Rule 4: repeat claimant.
    if previous_claim_count >= 3:
        if level != "High Risk":
            level = "Review Required"
        reasons.append(
            f"Customer has {previous_claim_count} previous claims (>= 3)."
        )

    # Rule 5: incomplete submission (missing description).
    if not description or not description.strip():
        if level != "High Risk":
            level = "Review Required"
        reasons.append("Claim description is missing or blank.")

    return level, reasons


def dashboard_counts():
    """Compute the six numbers required on the dashboard."""
    total = len(claims)
    submitted = sum(1 for c in claims.values() if c["status"] == "Submitted")
    under_review = sum(1 for c in claims.values() if c["status"] == "Under Review")
    approved = sum(1 for c in claims.values() if c["status"] == "Approved")
    rejected = sum(1 for c in claims.values() if c["status"] == "Rejected")
    flagged = sum(
        1 for c in claims.values() if c["risk_level"] in ("Review Required", "High Risk")
    )
    return {
        "total": total,
        "submitted": submitted,
        "under_review": under_review,
        "approved": approved,
        "rejected": rejected,
        "flagged": flagged,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/landing")
def landing():
    """Public Guard.In marketing landing page (no login required)."""
    return render_template("landing.html")


@app.route("/")
def index():
    """Home: send logged-in users to the dashboard, others to login."""
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page with a single hard-coded credential."""
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        error = "Invalid username or password. Please try again."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Clear the session and return to the login page."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    """Single dashboard view with the six required counts + recent claims."""
    counts = dashboard_counts()
    # Show the 5 most recently added claims (insertion order).
    recent = list(claims.values())[-5:][::-1]
    return render_template("dashboard.html", counts=counts, recent=recent)


@app.route("/policy", methods=["GET", "POST"])
@login_required
def policy():
    """Customer & policy intake form. Policy Number must be unique."""
    error = None
    success = None
    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        customer_id = request.form.get("customer_id", "").strip()
        policy_number = request.form.get("policy_number", "").strip()
        policy_type = request.form.get("policy_type", "").strip()
        policy_start_date = request.form.get("policy_start_date", "").strip()
        coverage_raw = request.form.get("coverage_amount", "").strip()

        # Required-field validation.
        if not all([customer_name, customer_id, policy_number,
                    policy_type, policy_start_date, coverage_raw]):
            error = "All policy fields are required."
        elif policy_number in policies:
            error = f"Policy number '{policy_number}' already exists. Use a unique policy number."
        else:
            # Coverage must be a non-negative number.
            try:
                coverage_amount = float(coverage_raw)
            except ValueError:
                error = "Coverage amount must be a valid number."
            else:
                if coverage_amount < 0:
                    error = "Coverage amount cannot be negative."
                else:
                    policies[policy_number] = {
                        "customer_name": customer_name,
                        "customer_id": customer_id,
                        "policy_number": policy_number,
                        "policy_type": policy_type,
                        "policy_start_date": policy_start_date,
                        "coverage_amount": coverage_amount,
                    }
                    success = f"Policy '{policy_number}' created successfully."

    return render_template(
        "policy.html",
        error=error,
        success=success,
        policies=list(policies.values()),
    )


@app.route("/claim", methods=["GET", "POST"])
@login_required
def claim():
    """Claim submission form. Classifies risk immediately and stores it."""
    error = None
    success = None
    result = None  # the just-created claim, shown with its flag + reasons

    if request.method == "POST":
        claim_id = request.form.get("claim_id", "").strip()
        policy_number = request.form.get("policy_number", "").strip()
        claim_type = request.form.get("claim_type", "").strip()
        amount_raw = request.form.get("claim_amount", "").strip()
        description = request.form.get("claim_description", "").strip()
        prev_raw = request.form.get("previous_claim_count", "").strip()

        # Claim ID is optional: blank means auto-generate (CLM-0001, ...).
        # A manually entered ID must still be unique.
        if not claim_id:
            claim_id = generate_claim_id()
        if claim_id in claims:
            error = f"Claim ID '{claim_id}' already exists. Use a unique ID or leave it blank to auto-generate."
        elif not all([policy_number, claim_type, amount_raw, prev_raw]):
            # Description is intentionally NOT in this required check:
            # a blank description is a valid submission that triggers the
            # "incomplete info -> Review Required" rule instead of an error.
            error = ("Policy number, claim type, claim amount and "
                     "previous claim count are required.")
        else:
            try:
                claim_amount = float(amount_raw)
            except ValueError:
                error = "Claim amount must be a valid number."
            else:
                try:
                    previous_claim_count = int(prev_raw)
                except ValueError:
                    # any non-integer is rejected
                    error = "Previous claim count must be a whole number (0, 1, 2, ...)."
                else:
                    if claim_amount < 0:
                        error = "Claim amount cannot be negative."
                    elif previous_claim_count < 0:
                        error = "Previous claim count cannot be negative."
                    else:
                        linked = policies.get(policy_number)
                        policy_exists = linked is not None
                        coverage = linked["coverage_amount"] if linked else None
                        risk_level, risk_reasons = classify_risk(
                            claim_amount, coverage, policy_exists,
                            previous_claim_count, description,
                        )
                        record = {
                            "claim_id": claim_id,
                            "policy_number": policy_number,
                            "customer_name": linked["customer_name"] if linked else "",
                            "claim_type": claim_type,
                            "claim_amount": claim_amount,
                            "claim_description": description,
                            "previous_claim_count": previous_claim_count,
                            "status": "Submitted",
                            "risk_level": risk_level,
                            "risk_reasons": risk_reasons,
                        }
                        claims[claim_id] = record
                        result = record
                        success = (f"Claim '{claim_id}' submitted "
                                   f"with flag: {risk_level}.")

    return render_template(
        "claim.html",
        error=error,
        success=success,
        result=result,
        policies=list(policies.values()),
    )


@app.route("/claims", methods=["GET"])
@login_required
def claims_list():
    """Claims table with search (Claim ID / Policy Number) + status filter."""
    query = request.args.get("q", "").strip().lower()
    status_filter = request.args.get("status", "").strip()

    filtered = list(claims.values())
    if query:
        filtered = [
            c for c in filtered
            if query in c["claim_id"].lower()
            or query in c["policy_number"].lower()
        ]
    if status_filter:
        filtered = [c for c in filtered if c["status"] == status_filter]

    return render_template(
        "claims.html",
        claims=filtered,
        query=request.args.get("q", ""),
        status_filter=status_filter,
        statuses=STATUS_CHOICES,
    )


@app.route("/claims/<claim_id>/status", methods=["POST"])
@login_required
def update_status(claim_id):
    """Change a claim's status (independent of its risk flag)."""
    record = claims.get(claim_id)
    if record is None:
        flash(f"Claim '{claim_id}' not found.", "error")
        return redirect(url_for("claims_list"))
    new_status = request.form.get("status", "").strip()
    if new_status not in STATUS_CHOICES:
        flash("Invalid status selected.", "error")
    else:
        record["status"] = new_status
        flash(f"Claim '{claim_id}' status updated to '{new_status}'.", "success")
    # Preserve the list-page search/filter context after the update.
    query = request.form.get("q", "")
    status_filter = request.form.get("status_filter", "")
    return redirect(url_for("claims_list", q=query, status=status_filter))


# ---------------------------------------------------------------------------
# Friendly error pages (no raw stack traces for the user)
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(_e):
    return render_template("error.html", code=404,
                           message="Page not found."), 404


@app.errorhandler(500)
def internal_error(_e):
    return render_template("error.html", code=500,
                           message="Something went wrong on our side."), 500


if __name__ == "__main__":
    # Render/Railway/Heroku set PORT env var. Local default is 5000.
    # Accessible at http://127.0.0.1:5000 after `python app.py`.
    import os

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
