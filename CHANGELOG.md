# Changelog

Notable changes to the web interface and repo setup. The bundled AChecker engine
(`bin/`, `src/`) is upstream code and is left as-is.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- This changelog.
- `templates/base.html` as a shared layout so `index.html` and `uploads.html`
  stop repeating the same head/header markup.
- Inline SVG icons for the theme toggle.
- "Nothing analysed yet" message on the history page.
- Upload size limit and auto-creation of the `uploads/` folder on startup.
- `Flask` and `pymongo` in `requirements.txt`.
- Some metadata in `setup.py` (description, url, license, classifiers).
- Env vars for config: `SECRET_KEY`, `FLASK_DEBUG`, `MONGO_URI`, `ACHECKER_TIMEOUT`.

### Changed

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
- The "Upload" control is a `<label>` for the file input instead of a button that
  needed JS to open the picker.
- Static files are served with `max-age=0` so edited CSS/JS show up on a normal
  refresh during development.
- Bigger `.gitignore`.

### Fixed

- `requirements.txt` didn't list Flask or pymongo, so the web app couldn't be
  installed from it.
- Theme toggle icon never changed (both states used the same image URL).
- Loading animation didn't really work. The form did a full page POST and a
  15-second timeout hid the loader. It now submits with `fetch()` and updates the
  results panel in place.
- Clicking "Upload" did nothing unless `scripts.js` loaded, so if the browser had
  an old copy cached you couldn't pick a file and Analyze reported "no file
  selected". The `<label>` opens the picker without any JS.
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
