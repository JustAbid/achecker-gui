# AChecker GUI

A small web interface for [AChecker](https://github.com/DependableSystemsLab/AChecker),
a static analysis tool that finds access control vulnerabilities in Ethereum
smart contracts.

AChecker is a command line tool. You give it a contract's EVM bytecode and it
prints the missing or violated access control checks it finds (plus unprotected
`SELFDESTRUCT` / `DELEGATECALL`). The output is hard to read unless you already
know EVM internals, so I put a Flask app in front of it.

With the web UI you can:

- upload a bytecode file from the browser
- run the analysis with one click, with a loading animation while it runs
- read the findings in a results panel instead of raw terminal output
- see a history of past analyses (stored in MongoDB)
- toggle a light/dark theme

This started as a college minor project in 2024. The analysis engine is not mine,
see [Credits](#credits) below.

## How it works

The browser uploads a file to the Flask app (`app.py`). The app saves it, records
it in MongoDB, and runs `bin/achecker.py -f <file> -b` as a subprocess. It parses
the tool's stdout into sections and sends them back to the page, which shows them
in the results panel.

The web UI always runs AChecker in bytecode mode (`-b`), so uploaded files need to
contain the runtime EVM bytecode as a hex string. There are a few examples in
[`samples/`](samples/). The command line version can also take Solidity source
directly.

## Requirements

- Python 3.8+ (tested on Ubuntu 20.04)
- MongoDB running locally on `mongodb://localhost:27017`
- `solc` / [`solc-select`](https://github.com/crytic/solc-select) if you want to
  analyze Solidity source from the CLI (not needed for bytecode)

## Setup

```bash
git clone https://github.com/JustAbid/achecker-gui.git
cd achecker-gui

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start MongoDB before running the web app if it isn't already running. The
service is called `mongodb` or `mongod` depending on how it was installed:

```bash
sudo systemctl start mongodb   # or: sudo systemctl start mongod
```

## Usage

### Web app

```bash
python3 app.py
```

Open http://127.0.0.1:5000, pick a bytecode file, and click Analyze.

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

The web app reads a few optional environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | `dev-only-not-secret` | Flask session key |
| `FLASK_DEBUG` | off | set to `1` for the debug server |
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `ACHECKER_TIMEOUT` | `300` | analysis time limit in seconds |
| `ACHECKER_TZ` | `Europe/Berlin` | timezone for history timestamps |

If MongoDB isn't running the analysis still works, you just don't get history.

## Project layout

```
achecker-gui/
├── app.py               Flask app (upload, analyze, history)
├── bin/achecker.py      AChecker CLI entry point
├── src/                 AChecker analysis engine
│   ├── cfg/             CFG recovery, disassembly, bundled Rattle
│   ├── evm/             symbolic EVM
│   ├── explorer/        path exploration
│   ├── flow/            data-flow / taint analysis and the detectors
│   └── util/            helpers
├── templates/
│   ├── base.html        shared layout
│   ├── index.html       upload + results page
│   ├── _results.html    results fragment (returned to the async upload)
│   └── uploads.html     history page
├── static/
│   ├── css/styles.css
│   └── js/scripts.js
├── samples/             example bytecode files (incl. CVE-2021-34273)
├── uploads/             runtime uploads (git-ignored)
├── CHANGELOG.md
├── requirements.txt
└── setup.py
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

Only the Flask app, the templates, and the static files are my work.

## License

MIT, see [LICENSE](LICENSE). The bundled Rattle and teEther code keep their own
licenses (noted in the LICENSE file).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
