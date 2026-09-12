# Insurance Claim Management & Risk Review System

Simple Flask web app for submitting, reviewing and tracking insurance claims.
Educational project — Flask routing, forms, rule-based logic, in-memory storage (no database).

## Quick start

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in a browser.

## Login

Single hard-coded staff credential (per spec, no real auth):

- Username: `admin`
- Password: `admin123`

Unauthenticated visits to `/dashboard`, `/policy`, `/claim`, `/claims` redirect to `/login`.

## Workflow

1. **New Policy** — save customer + policy. Policy Number must be unique.
2. **New Claim** — submit a claim against a policy number.
   Claim ID is **optional**: leave it blank and the system auto-generates
   `CLM-0001`, `CLM-0002`, …; a manually entered ID must be unique.
3. Each claim is instantly classified **Normal / Review Required / High Risk**
   with human-readable reasons shown on the claim form and the claims table.
4. **Claims** — search by Claim ID / Policy Number (partial match), filter by
   status, change status (Submitted → Under Review → Approved / Rejected).
   Risk flag and status are independent and use different badge colours.
5. **Dashboard** — total, submitted, under review, approved, rejected, and
   flagged-for-review (Review Required + High Risk) counts.

All data is in-memory Python dicts and resets on restart.

## Claim-review rules (Section 7 defaults)

| Rule | Trigger | Flag |
|---|---|---|
| Unusually high amount | Claim > 80% of linked policy coverage | High Risk |
| High amount | Claim > 50% (and ≤ 80%) of coverage | Review Required |
| Unknown policy | Policy number not on file | Review Required |
| Repeat claimant | Previous claim count ≥ 3 | Review Required |
| Incomplete | Description blank | Review Required |

Most severe flag wins (High Risk > Review Required > Normal); all fired
reasons are displayed.

## Project structure

```
insurance_claim_app/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── policy.html
│   ├── claim.html
│   ├── claims.html
│   └── error.html
└── static/
    └── style.css
```

## Validation

Required fields, numeric coverage/claim amounts, non-negative values, and
whole-number previous-claim counts are enforced with friendly messages —
the app never exposes a stack trace (custom 404/500 page).
