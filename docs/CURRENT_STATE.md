

# CURRENT_STATE

## Code prompt

### Architecture & Separation of Concerns
- Establish an architecture that sets explicit boundaries between UI, domain, and infrastructure layers. This should be reflected in the directory structure.
- Avoid dumping new files in the project root; just keep main.py there.
- `main.py` or `main.dart` must not contain any wiring, domain logic, or infrastructure.
- Keep UI wiring, domain logic, and infrastructure separated. Domain must not import infra or UI.
- Prefer thin orchestrators and small, focused services. Use explicit service helpers for UI side effects.
- Avoid direct dialog/widget mutations across layers; use adapters/services (for example, `CategoryManagerUIService`, `AddEditStateService`).
- Keep init/builders as composition roots; do not leak logic into UI builders.
- Prefer explicit dependencies via small dataclasses/services rather than hidden attribute reach-through.

### Readability & Maintainability
- Use clear, short functions with a single responsibility. Extract helpers when logic grows.
- Avoid `getattr`/duck typing in production flow unless truly necessary; prefer adapters/registries.
- Write defensive UI code (best-effort; never crash), but keep error handling narrow and intentional.
- Keep naming consistent with existing patterns: `*Service`, `*Controller`, `*Coordinator`, `*Effects`, `*Rules`.
- Always add explicit error types in try/catch.
- Avoid code duplication.
- Avoid overly clever abstractions.

### File Size Constraint
- Keep each file under 300 lines. If a file approaches 300, split it into focused modules.
- Make a script to do this at regular intervals, adjusted for the local project.

Example:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="${1:-.}"
if ! command -v rg >/dev/null 2>&1; then
  echo "rg (ripgrep) is required." >&2
  exit 1
fi
rg --files "$ROOT_DIR" \
  | rg -v "^${ROOT_DIR}/assets/" \
  | rg -v "^${ROOT_DIR}/pubspec.lock$" \
  | rg -v "^${ROOT_DIR}/ios/Runner.xcodeproj/project.pbxproj$" \
  | rg -v "^${ROOT_DIR}/macos/Runner.xcodeproj/project.pbxproj$" \
  | xargs wc -l \
  | awk '$2 != "total" && $1 > 300 {print $1, $2; found=1} END{exit found?1:0}'
```

### Testing & Refactors
- Always consider adding new tests, even small ones, and always make appropriate suggestions.
- Add small pure tests for new services/helpers when behavior might regress.
- Preserve behavior; refactors should be test-driven and avoid hidden side effects.
- Add Flutter integration tests to test the UI, especially for iOS.
- Consider using Patrol for Android UI tests.
- Remind me to run tests when appropriate.
- Remind me to run manual tests when appropriate.
- Avoid leaving brittle wrappers behind when refactoring code.
- Always start major refactoring in a new branch.

### Coding Style
- Prefer explicit imports. Avoid large inline logic inside UI event handlers.
- Keep log noise low; log failures only in hot paths.

### Output
- Make changes in one pass; keep diffs minimal and focused.
- Maintain a `CURRENT_STATE.md` file that contains this prompt at the top of the file, then the state of the code base architecture, then a report of running any tests.

### Debugging
- Add a debugging code system that allows all debug code to be turned off.
- When debug code is added, make sure it complies with this prerequisite.

### Git
- Remind me to commit and push when appropriate.
- Before doing large-scale refactoring, remind me to change to a refactoring branch.

## If a database is required

### Database requirements
- Use the built-in `sqlite3` library unless there is a strong reason otherwise.
- Organize the code clearly, with separation between:
  1. database connection/setup
  2. schema creation
  3. CRUD operations
  4. utility/helper functions
- Include clear comments throughout.
- Use parameterized queries everywhere to prevent SQL injection.
- Use context managers or another safe pattern to ensure connections and transactions are handled correctly.
- Include proper error handling for database operations.
- Design the code so it can be reused in a larger application.

### Database expectations
- Create the database file if it does not already exist.
- Define a schema using `CREATE TABLE IF NOT EXISTS`.
- Include a primary key for each table.
- Add appropriate foreign keys, unique constraints, default values, and indexes where sensible.
- Enable foreign key enforcement.
- Include a function to initialize the database schema.

### Database coding expectations
- Use classes or well-structured functions, whichever is more appropriate for clarity and maintainability.
- Include type hints where reasonable.
- Avoid overly clever abstractions; prefer readable, practical code.
- Make the design easy to extend with additional tables later.
- Return query results in a convenient format, such as tuples, dictionaries, or lightweight objects, and be consistent.

### Database functionality to include
- Connect to the SQLite database.
- Initialize schema.
- Insert records.
- Fetch one record.
- Fetch multiple records.
- Update records.
- Delete records.
- Optionally search/filter records.
- Optionally support soft delete if appropriate.

### Database testing/demo expectations
- Include a short example showing how to initialize the database and perform basic CRUD operations.
- Include sample table definitions and example usage data.

### Database output expectations
- After the code, briefly explain the structure and design decisions.
- Do not omit important implementation details.

## Code base architecture state

Assessment date: 2026-07-10

### Overall status
- The project is now a small Python/Tkinter offer-code assignment app backed by `data/offer-codes.yaml`.
- `main.py` is thin and only calls the app composition root.
- The code is split into explicit architecture layers:
  - `offer_codes/domain`: record model, domain errors, and completion rules.
  - `offer_codes/application`: date provider, repository/email protocols, `AuthService`, `OfferCodeService`, and `OfferCodeEmailService`.
  - `offer_codes/infrastructure`: YAML file repositories, `.env` loader, SMTP config, and SMTP email sender.
  - `offer_codes/ui`: login dialog, Tkinter form, controller, and dialog effects.
  - `offer_codes/app`: composition root.

### Current behavior
- The app loads the first available record from `data/offer-codes.yaml`.
- The app shows a simple modal login dialog at startup and authenticates users from `data/users.yaml`; user and password matching is case-insensitive.
- The top of the app has dry-run/issue radio buttons. When dry run is selected, a 26pt bold red `Dry run` warning is shown; when issue mode is selected, a 26pt bold red `Offer codes will be issued!` warning is shown.
- A record is considered available when `U3A_number`, `email`, and `issued` are blank.
- The form displays `offer_number` as read-only.
- The form has hinted `first_name` and `last_name` fields directly below `offer_number`; both fields are persisted to `data/offer-codes.yaml`.
- Before saving, first and last names are normalized to capitalized words and email addresses are normalized to lowercase.
- The `Issued` field defaults to today's ISO date and has an icon-only button using a 27px render of `assets/icons/calendar-icon-symbol-sign-vector.jpg` for the built-in Tkinter calendar popup.
- The save button is enabled only when `U3A_number`, `first_name`, `last_name`, `email`, and `Issued` are completed.
- The Ready status displays the number of offer codes remaining.
- Dry-run mode is enabled by default: clicking Save sends the offer-code email, advances to the next offer code for the current app session, but does not write data to `data/offer-codes.yaml`.
- When dry-run mode is disabled, clicking Save sends the offer-code email and then writes the issued record to `data/offer-codes.yaml`.
- While email is being generated and sent, the form displays an inline progress bar beside Save and disables Save. SMTP sending runs on a background thread so the Tkinter UI can continue repainting.
- Real saved records cannot issue more than one offer code to the same `U3A_number`; dry-run advancement intentionally ignores this uniqueness rule. In real issue mode, duplicate U3A numbers are blocked before email is sent.
- Local SMTP settings are loaded from an ignored `.env` file at startup. Safe placeholder values are documented in `.env.example`.

### File-size constraint compliance
- Prompt target: each file must be under 300 lines.
- `scripts/check_file_sizes.sh` enforces the 300-line threshold and excludes source-data CSV files and Python bytecode caches.
- Result: pass as of this assessment.

### Testing and refactor posture
- Focused tests cover login authentication, user YAML parsing, application behavior, U3A-number uniqueness for saved records, YAML persistence, dry-run and real-issue controller paths, email message creation, SMTP config, and `.env` loading.
- The Tkinter UI has not been manually exercised in this pass.
- No database is used; the existing YAML file remains the source of truth.

### Debug gating status
- No debug logging system has been added because no debug code was introduced.

## Tests run

Run date: 2026-07-10

1. `python3 -m pytest`
- Result: pass (`20` tests passed).

2. `python3 -m compileall main.py offer_codes tests`
- Result: pass.

3. `./scripts/check_file_sizes.sh .`
- Result: pass after excluding source-data CSV files.

Notes:
- Manual Tkinter testing is still recommended: run `python3 main.py`, complete one record, and confirm the email sends while `data/offer-codes.yaml` remains unchanged.
