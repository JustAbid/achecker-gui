# Changelog

Notable changes to the web interface and repo setup. The bundled AChecker engine
(`bin/`, `src/`) is upstream code; the only edits there disable stray debug
`print()` statements, the analysis logic is untouched.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **Structured results.** AChecker's console output is parsed into findings —
  vulnerability type, affected function, a severity badge, the offending EVM
  instruction, and a plain-English description — shown as cards with a summary
  banner ("2 access-control issues found") instead of a raw text dump.
- **Useful history.** Each analysis stores its full result. The history page
  shows a clean / N-issues badge per row, rows link to the saved report, and a
  report can be downloaded as JSON or Markdown. Old rows are marked "legacy".
- **"Try a sample" buttons** on the home page for the bundled example contracts.
- **Test suite** (`tests/`, `pytest`) covering the output parser, the routes
  (with a stubbed engine), the Markdown export, and the MongoDB-down fallbacks.
- **CI**: GitHub Actions runs `ruff` + `pytest` on Python 3.8 and 3.11.
- **Docker**: `Dockerfile` + `docker-compose.yml` bring up the app, MongoDB, and
  a solc build with one command.
- `requirements-web.txt` / `requirements-dev.txt` so the web layer can be
  installed without the heavy analysis-engine dependencies.
- `.env` support (`python-dotenv`) and `.env.example`; `pyproject.toml` for ruff
  and pytest config.
- This changelog.
- `templates/base.html` as a shared layout so `index.html` and `uploads.html`
  stop repeating the same head/header markup.
- Inline SVG icons for the theme toggle.
- "Nothing analysed yet" message on the history page.
- Upload size limit and auto-creation of the `uploads/` folder on startup.
- `Flask` and `pymongo` in `requirements.txt`.
- Some metadata in `setup.py` (description, url, license, classifiers).
- Env vars for config: `SECRET_KEY`, `FLASK_DEBUG`, `MONGO_URI`,
  `ACHECKER_TIMEOUT`, `ACHECKER_TZ`.
- Static file URLs get a `?v=<mtime>` suffix so an edited CSS/JS is always
  refetched.

### Changed

- The web app is now an `achecker_gui/` package with an application factory
  (`create_app()`), a blueprint, and separate modules for the parser
  (`report.py`), the engine call (`analysis.py`), and history (`store.py`).
  `app.py` is a thin entry point; production runs under gunicorn.
- `/view-uploads` is now `/history` (the old path redirects).
- Silenced leftover debug `print()` calls in the vendored engine
  (`src/project.py`, `src/cfg/rattle/`) that were dumping raw instruction lists
  onto stdout for some contracts. The analysis logic is unchanged.
- Moved the sample `.code` files from `uploads/` to `samples/`. `uploads/` is now
  only used at runtime.
- `app.py` builds the results from a data structure rendered by Jinja instead of
  concatenating HTML strings. Output is escaped now.
- Analysis subprocess runs with `sys.executable`, a fixed working directory and a
  timeout.
- Templates load CSS/JS through `url_for`.
- Theme class is set on `<html>` by a tiny inline script before paint, so dark
  mode doesn't flash white on load.
- Results text is left-aligned. Dropped the fixed 250px bottom padding.
- The file input is a transparent overlay on the "Upload" button, so the picker
  works without JS and a double-click in the file dialog is handled natively.
- Every response sends `Cache-Control: no-store` so the browser doesn't show a
  stale page (e.g. old history right after an analysis, or old CSS/JS).
- Failed history writes are logged to the console instead of silently ignored.
- New history entries are timestamped in Berlin time, 12-hour format. Existing
  rows are untouched.
- The history list is sorted by `_id` (which is time-ordered) instead of the
  `upload_time` string, so ordering is correct no matter the timestamp format.
- Bigger `.gitignore`.

### Fixed

- `requirements.txt` didn't list Flask or pymongo, so the web app couldn't be
  installed from it.
- Theme toggle icon never changed (both states used the same image URL).
- Loading animation didn't really work. The form did a full page POST and a
  15-second timeout hid the loader. It now submits with `fetch()` and updates the
  results panel in place.
- Clicking "Upload" did nothing unless `scripts.js` loaded, so a cached old copy
  left you unable to pick a file and Analyze said "no file selected". The picker
  is a plain `<input type="file">` now, no JS involved.
- Double-clicking a file in the OS dialog didn't register the selection (you had
  to single-click and then press Open). The overlay input handles it, plus JS
  ignores the stray click some Linux setups fire when the dialog closes.
- New analyses weren't showing at the top of the history: entries are sorted by
  `_id` now, so the most recent one is always first.
- The history page could show an out-of-date list after analysing more files
  because the browser cached it. Fixed by the `no-store` header.
- The "Upload" control showed the raw browser file picker ("Choose file / no file
  chosen") when an old CSS was cached. The `?v=` suffix stops that.
- Upload errors redirected to `/upload`, which is POST only, so you got a 405.
  They go back to the home page with a message now.
- Uploaded file names are cleaned with `secure_filename()` (was a path traversal
  hole).
- A non-zero exit code / stderr from AChecker is shown instead of a blank panel.
- App no longer 500s with a traceback when MongoDB is down. History is skipped,
  analysis still runs.
- ANSI codes are stripped with a regex instead of replacing two specific ones.

### Removed

- `AChecker.egg-info/` and `__pycache__/` from the repo.
- Hardcoded `secret_key` and `debug=True`.
- `flash()` calls that no template ever displayed.
- Theme icons loaded from img.icons8.com.

## [0.1.0] - 2026-09-06

First commit. The project as it was after the 2024 minor project.

- AChecker engine (`bin/achecker.py`, `src/`): static detection of missing and
  violated access control checks in EVM bytecode.
- Flask web interface: upload, analyze, results panel, MongoDB history, light/dark
  theme toggle.
- `README.md`, `LICENSE` (MIT + notices for the bundled Rattle and teEther code),
  `.gitignore`.
