# AChecker GUI

[![CI](https://github.com/JustAbid/achecker-gui/actions/workflows/ci.yml/badge.svg)](https://github.com/JustAbid/achecker-gui/actions/workflows/ci.yml)

A web interface for [AChecker](https://github.com/DependableSystemsLab/AChecker),
a static analysis tool that finds access control vulnerabilities in Ethereum
smart contracts.

AChecker is a command line tool. You give it a contract's EVM bytecode and it
prints the missing or violated access control checks it finds (plus unprotected
`SELFDESTRUCT` / `DELEGATECALL`). The output is hard to read unless you already
know EVM internals, so I put a Flask app in front of it.

With the web UI you can:

- upload a bytecode file, or analyse one of the bundled samples with one click
- read the findings as cards — vulnerability type, affected function, severity,
  the offending EVM instruction, and a plain-English description — with a summary
  line like *"2 access-control issues found (1 high, 1 medium)"*
- browse a history of past analyses (stored in MongoDB), reopen any saved report,
  and download it as JSON or Markdown
- toggle a light/dark theme

This started as a college minor project in 2024. The analysis engine is not mine,
see [Credits](#credits) below.

## How it works

The browser posts a file to the Flask app, which saves it, runs
`bin/achecker.py -f <file> -b` as a subprocess, parses the tool's stdout into a
structured report, stores it in MongoDB, and renders it. The web UI always runs
AChecker in bytecode mode (`-b`), so uploaded files must contain the runtime EVM
bytecode as a hex string — there are examples in [`samples/`](samples/). The
command line version also takes Solidity source directly.

## Requirements

- Python 3.8+ (tested on Ubuntu 20.04)
- MongoDB (optional — without it the analysis still runs, you just get no history)
- `solc` / [`solc-select`](https://github.com/crytic/solc-select) only if you
  analyse Solidity source from the CLI

## Run it with Docker

```bash
docker compose up --build
```

This starts the app on <http://127.0.0.1:5000> plus a MongoDB container. Config
can be overridden with a `.env` file (see [`.env.example`](.env.example)).

## Run it locally

```bash
git clone https://github.com/JustAbid/achecker-gui.git
cd achecker-gui

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start MongoDB if it isn't already running (`sudo systemctl start mongodb`, or
`mongod`), then:

```bash
python3 app.py            # dev server on http://127.0.0.1:5000
```

For production the app runs under gunicorn:

```bash
gunicorn "achecker_gui:create_app()" --bind 0.0.0.0:5000 --timeout 600
```

### Command line

```bash
python3 bin/achecker.py -f samples/CVE-2021-34273.code -b -m 8
```

| Flag | Meaning |
|------|---------|
| `-f` | path to the contract file |
| `-b` | input is EVM bytecode (leave it off for Solidity source) |
| `-m` | max memory in GB (default 6) |
| `-sf` | save file base name |

## Configuration

Read from the environment, or a `.env` file. All optional.

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | `dev-only-not-secret` | Flask session key |
| `FLASK_DEBUG` | off | set to `1` for the debug server |
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `MONGO_DB` | `achecker_db` | database name |
| `ACHECKER_TIMEOUT` | `300` | analysis time limit, seconds |
| `ACHECKER_MEMORY_GB` | `6` | memory ceiling passed to AChecker |
| `ACHECKER_TZ` | `Europe/Berlin` | timezone for history timestamps |

## Development

```bash
pip install -r requirements-dev.txt   # web layer only, no analysis engine
ruff check .
pytest
```

`requirements-dev.txt` skips the heavy engine dependencies (z3, pysha3, Cython…),
so the tests and CI stay fast — the route tests stub out the subprocess and the
parser tests run against captured fixtures in [`tests/fixtures/`](tests/fixtures).

## Project layout

```
achecker-gui/
├── app.py                 dev-server entry point (create_app())
├── achecker_gui/          the web application
│   ├── __init__.py        application factory
│   ├── config.py          settings from env / .env
│   ├── views.py           routes (blueprint)
│   ├── report.py          parse AChecker output -> structured Report
│   ├── analysis.py        run the AChecker subprocess
│   ├── store.py           MongoDB history (degrades gracefully)
│   ├── reporting.py       Markdown export
│   ├── templates/
│   └── static/
├── bin/achecker.py        AChecker CLI entry point         ┐
├── src/                   AChecker analysis engine          ├─ upstream
│   └── cfg/rattle/        bundled Rattle (SSA recovery)     ┘
├── samples/               example bytecode (incl. CVE-2021-34273)
├── tests/                 pytest suite + output fixtures
├── Dockerfile, docker-compose.yml
├── requirements*.txt
└── CHANGELOG.md
```

## Credits

The engine is AChecker by Asem Ghaleb, Julia Rubin, and Karthik Pattabiraman
(University of British Columbia), from their ICSE 2023 paper:

> A. Ghaleb, J. Rubin, and K. Pattabiraman, "AChecker: Statically Detecting
> Smart Contract Access Control Vulnerabilities," 2023 IEEE/ACM 45th
> International Conference on Software Engineering (ICSE), 2023.

```bibtex
@inproceedings{ghaleb2023achecker,
  title     = {AChecker: Statically Detecting Smart Contract Access Control Vulnerabilities},
  author    = {Ghaleb, Asem and Rubin, Julia and Pattabiraman, Karthik},
  booktitle = {2023 IEEE/ACM 45th International Conference on Software Engineering (ICSE)},
  year      = {2023},
  publisher = {IEEE}
}
```

Upstream repo: https://github.com/DependableSystemsLab/AChecker

The `achecker_gui/` package, the templates, the static files, and the tests are
my work. `bin/` and `src/` are upstream (the only change there is silencing a few
stray debug prints).

## License

MIT, see [LICENSE](LICENSE). The bundled Rattle and teEther code keep their own
licenses (noted in the LICENSE file).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
