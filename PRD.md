# Product Requirements Document (PRD)

## Insurance Claim Management & Risk Review System

**Document owner:** Internship Project — ARINSA AI MINDS
**Source documents:** `Insurance_Claim_Management_Project.pdf` (functional spec), `Instructions.pdf` (submission/process spec)
**Status:** Draft for implementation

---

## 1. Purpose & Background

Build a simple Flask-based web application that lets a user submit, review and track insurance claims. The system collects basic policy and claim information and applies simple, transparent Python rules to flag claims that may need additional review, rather than approving/rejecting anything automatically. The project's purpose is educational: it should demonstrate Flask routing, form handling, conditional business logic, and in-memory record management without a database.

## 2. Goals

- Provide a working, end-to-end claim intake → risk flag → review → status update workflow.
- Keep the stack intentionally minimal (Flask, Jinja, HTML, basic CSS, in-memory Python data structures).
- Make the rule-based risk logic visible and explainable (show *why* a claim was flagged, not just the flag).
- Produce a submission package that satisfies the process requirements in `Instructions.pdf` (folder structure, README, requirements.txt, screen recording, ZIP naming).

## 3. Non-Goals / Out of Scope

- No real authentication system, password hashing, or user management — a single hard-coded credential is sufficient.
- No persistent storage (database, files-as-DB, ORM). All data lives in memory and resets on restart.
- No real underwriting, actuarial, or fraud-detection logic — the "risk rules" are simple, illustrative, rule-based checks, not a production risk engine.
- No external integrations (payment, email, notifications, third-party APIs).
- No multi-user concurrency guarantees — this is a single-session demo app.

## 4. Users & Access

| Role | Description | Access |
|---|---|---|
| Claims Staff (single role) | The only user type. Logs in with a shared, hard-coded credential and can create policies, submit claims, review/search claims, and update claim status. | Full access to all pages after login |

There is no admin/staff distinction and no self-service customer portal — this is an internal tool.

## 5. Functional Requirements

### 5.1 Technology Requirements
- Python 3.x
- Flask
- HTML5
- Basic CSS
- Jinja2 templates
- No database — in-memory Python data structures (e.g., dictionaries/lists) hold all policy and claim records for the lifetime of the running process.

### 5.2 Login UI
- A dedicated login page is shown before any part of the claim system is accessible.
- Fields: **Username**, **Password**.
- Invalid credentials show a clear, on-screen error message (no crash, no silent failure).
- Successful login redirects the user to the claim **dashboard**.
- Authentication uses one hard-coded username/password pair. Database-backed auth is explicitly not required.
- Unauthenticated access to any internal page (dashboard, policy form, claim form, claims list) must redirect to login.

### 5.3 Customer & Policy Information
A form must collect and store:
- Customer Name
- Customer ID
- Policy Number *(must be unique — duplicate policy numbers are rejected with an error)*
- Policy Type
- Policy Start Date
- Policy Coverage Amount (numeric, non-negative)

### 5.4 Claim Submission
A form must allow the user to submit a claim containing:
- Claim ID
- Policy Number *(should reference an existing policy where possible)*
- Claim Type
- Claim Amount (numeric, non-negative)
- Claim Description
- Previous Claim Count (integer, non-negative)

> **Implementation note:** Claim ID may be entered manually or generated automatically by the system (e.g., `CLM-0001`) to guarantee uniqueness. Either approach satisfies the requirement as long as every stored claim record has a Claim ID; the design decision should be documented in the README.

### 5.5 Claim Review & Risk Flag
- All submitted claims are displayed in a table.
- Each claim is passed through a basic, rule-based check at submission time (or on demand) to compute a review flag.
- Claims are classified into exactly one of three levels:
  - **Normal**
  - **Review Required**
  - **High Risk**
- The system displays the main reason(s) that produced the flag (not just the flag itself).
- Example rule ideas (the actual thresholds are an implementation detail, but the rule *types* below must be represented):
  - Claim Amount is unusually high compared with the linked policy's Coverage Amount.
  - The customer/policy has multiple previous claims recorded.
  - Required claim information is incomplete (e.g., missing description).
- The claim's **status** can be updated independently of its risk flag (risk flag explains *why* review might be needed; status tracks *where the claim is* in its lifecycle).

### 5.6 Claim Status
Each claim has a status, one of:
1. Submitted
2. Under Review
3. Approved
4. Rejected

The UI must allow this status to be changed after submission.

### 5.7 Dashboard
A single dashboard view must show, at minimum:
- Total claims
- Submitted claims (count)
- Claims under review (count)
- Approved claims (count)
- Rejected claims (count)
- Claims flagged for additional review (Review Required + High Risk, count)

### 5.8 Search & Filtering
On the claims list:
- Search by **Claim ID** or **Policy Number** (partial match acceptable).
- Filter by **status**.
- If no claim matches the current search/filter, display a clear "no matching claim found" message instead of an empty or broken table.

### 5.9 Validation & Error Handling
- All required fields must be validated before a record is accepted.
- Claim Amount and Policy Coverage Amount must be valid numeric values.
- Negative monetary values must be rejected.
- Previous Claim Count must be a valid non-negative whole number.
- All error conditions must show a clear, human-readable message and must **not** crash the application (no unhandled stack traces surfaced to the user).
- Unexpected errors (404 / 500) should be caught by a friendly fallback page rather than a raw server error.

### 5.10 UI Requirements
- Clean, simple, insurance-oriented visual design using HTML and basic CSS (no heavy frontend framework required).
- Claim information is displayed using tables or cards.
- Claim status and risk/review classification must be visually distinguishable from each other (e.g., separate badges/colors) so a user doesn't confuse "what stage is this claim at" with "does this claim need review."
- Simple, persistent navigation between: Dashboard, Policy form, Claim form, and Claims list.

## 6. Data Model (In-Memory)

No database is used. Suggested in-memory shape:

**Policy record**
```
{
  "customer_name": str,
  "customer_id": str,
  "policy_number": str,   # unique key
  "policy_type": str,
  "policy_start_date": str (ISO date),
  "coverage_amount": float  # >= 0
}
```

**Claim record**
```
{
  "claim_id": str,            # unique key
  "policy_number": str,       # links to a Policy record
  "customer_name": str,       # denormalized for display
  "claim_type": str,
  "claim_amount": float,      # >= 0
  "claim_description": str,
  "previous_claim_count": int,# >= 0
  "status": str,               # Submitted | Under Review | Approved | Rejected
  "risk_level": str,           # Normal | Review Required | High Risk
  "risk_reasons": list[str]    # human-readable reasons behind the risk_level
}
```

## 7. Business Rules — Risk Classification (Reference Logic)

The following is one valid, concrete implementation of the "example rule ideas" in the spec. Thresholds are tunable and should be documented, not hard requirements of the brief itself.

| # | Rule | Trigger | Resulting flag |
|---|---|---|---|
| 1 | Unusually high claim amount | Claim Amount > 80% of the linked policy's Coverage Amount | High Risk |
| 2 | High claim amount | Claim Amount > 50% (and ≤ 80%) of Coverage Amount | Review Required |
| 3 | Unknown/unlinked policy | Policy Number on the claim does not match any recorded policy | Review Required |
| 4 | Repeat claimant | Previous Claim Count ≥ 3 | Review Required |
| 5 | Incomplete submission | Claim Description missing/blank | Review Required |

- If multiple rules fire, the claim takes the **most severe** resulting flag (High Risk > Review Required > Normal).
- If no rule fires, the claim is **Normal**.
- All reasons that fired must be shown to the user, not just the final flag.

## 8. Suggested Project Structure

```
insurance_claim_app/
│
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── policy.html
│   ├── claim.html
│   └── claims.html
└── static/
    └── style.css
```

(Additional templates such as a shared `base.html` layout or an `error.html` fallback page are reasonable additions, not deviations from spec.)

## 9. Non-Functional Requirements

- **Simplicity first:** favor readable, well-commented Python over cleverness — this is an educational project and the author must be able to explain every part of it.
- **Resilience:** invalid input must never crash the running server.
- **Statelessness across restarts:** it's acceptable (and expected) that data resets when the app restarts, since there is no database.
- **Portability:** the app must run locally via `python app.py` using only the packages listed in `requirements.txt`, inside a Python virtual environment.

## 10. Expected Learning Outcomes

- Understand Flask routing and multi-page application flow.
- Use GET and POST requests with HTML forms.
- Apply Python functions and conditional logic to a business problem.
- Implement rule-based risk/review logic.
- Manage records without using a database.
- Implement validation, search and error handling.

## 11. Deliverables & Submission Requirements

### 11.1 Project deliverables (from the functional spec)
- Complete Flask project source code.
- All HTML and CSS files used by the application.
- A short README explaining how to run the application.
- Screenshots showing the login, dashboard, policy, claim and review features.
- A brief explanation of the claim-review rules and application workflow (can live in the README).

### 11.2 Development process (from the submission instructions)
1. Install Python 3.x.
2. Install VS Code, with the Python extension (and any other extensions needed).
3. Create a dedicated project folder and open it in VS Code.
4. Create and use a Python virtual environment (e.g., `python -m venv venv`).
5. Install **all** required dependencies (not just Flask) into the virtual environment.
6. Build the Flask app per the functional spec (Sections 5–10 above).
7. Build the HTML/CSS UI, including the login screen and all required forms/pages.
8. Implement the required logic: validations, workflows, rules, processing, outputs.
9. Validate inputs and handle invalid/missing/unexpected input without crashing.
10. Test the full application end-to-end: all forms, inputs, outputs, workflows.
11. Debug and fix issues found during testing before submission.
12. If the app produces any output files/reports/exports, place them in an `output/` folder (otherwise this folder is omitted).
13. Record **one** screen recording of the completed, running application — starting from the home/login screen and demonstrating the main workflow and all major features (must show the working app, not just source code; MP4 or another common video format).
14. Generate `requirements.txt` (e.g., `pip freeze > requirements.txt`).
15. Zip the complete project as `project_name.zip` (the project name should match the assigned project).
16. Assemble the final `submit_file.zip` containing:
    - `project_name.zip` (full project ZIP)
    - `output/` folder (only if the project generates output files)
    - the screen recording file (MP4 or equivalent)
17. Verify before submission: the project ZIP opens correctly and contains all required source files; the output folder (if present) contains the expected generated files; the recording clearly demonstrates the completed app.
18. Submit only the single `submit_file.zip`.

### 11.3 Final submission structure

```
submit_file.zip
│
├── project_name.zip
│   └── project_name/
│       ├── app.py
│       ├── templates/
│       ├── static/
│       ├── README.md
│       ├── requirements.txt
│       └── other required project files
│
├── output/                      # only if the project generates output files
│   └── generated files
│
└── screen_recording.mp4         # or another commonly supported video format
```

### 11.4 Integrity / evaluation expectations
- The project must be the author's own implementation.
- Official documentation, tutorials, and other learning resources may be used to understand concepts — but a complete, un-understood, copied solution must not be submitted.
- The author must be able to explain the project's structure, code, logic, and workflow during evaluation.
- Only files actually required for the project and its submission should be included (no stray/unused files).

## 12. Acceptance Criteria (Definition of Done)

A build satisfies this PRD when all of the following are true:

- [ ] Login page rejects bad credentials with a visible error and accepts the hard-coded credential, redirecting to the dashboard.
- [ ] Unauthenticated users cannot reach dashboard/policy/claim/claims pages directly.
- [ ] A policy can be created with all required fields; duplicate Policy Numbers are rejected.
- [ ] A claim can be submitted with all required fields and is immediately classified as Normal / Review Required / High Risk, with reasons shown.
- [ ] The three example rule types (high amount vs. coverage, repeat claims, incomplete info) are all represented in the logic.
- [ ] Claim status can be changed across Submitted → Under Review → Approved/Rejected.
- [ ] Dashboard shows all six required counts and they update as claims are added/changed.
- [ ] Claims list supports search by Claim ID/Policy Number and filter by status, with a graceful "no results" state.
- [ ] Negative amounts, non-numeric amounts, and missing required fields are all rejected with clear messages and no crash.
- [ ] Navigation between Dashboard / Policy / Claim / Claims is present on every internal page.
- [ ] `requirements.txt`, README, and screenshots (or recording) are included in the final submission package per Section 11.

## 13. Open Questions / Decisions Left to the Implementer

- Exact numeric thresholds for "unusually high" claim amount and "multiple" previous claims (Section 7 offers a reasonable default: 50%/80% and ≥3).
- Whether Claim ID is user-entered or system-generated (either is acceptable; document the choice).
- Whether an additional policy-listing view is included beyond what's strictly required (nice-to-have, not required).
