# AChecker GUI

A web front end for **[AChecker](https://github.com/DependableSystemsLab/AChecker)**, the
static-analysis tool that detects **access control vulnerabilities** in Ethereum
smart contracts.

AChecker itself is a command-line utility: you hand it a contract's EVM bytecode
and it reports missing or violated access-control checks (and unprotected
`SELFDESTRUCT` / `DELEGATECALL`). Its raw output is dense and hard to read for
anyone who isn't already deep in EVM internals.

This project wraps that CLI in a small Flask application so you can:

- upload a contract bytecode file from the browser,
- run the analysis with one click and watch a loading animation while it works,
- read the findings in a formatted results panel,
- browse a history of everything you've analysed (stored in MongoDB),
- switch between a light and a dark theme.

> This was built as an undergraduate minor project (2024). The analysis engine is
> not my work — see [Credits](#credits).

---

## How it works

```
Browser ──upload──▶ Flask (app.py) ──▶ bin/achecker.py -f <file> -b ──▶ src/ engine
   ▲                     │                        │
   └── formatted HTML ◀──┴── parse stdout ◀───────┘
                         │
                         └──▶ MongoDB (filename + timestamp)  ──▶ /view-uploads
```

The web UI runs AChecker in **bytecode mode** (`-b`), so uploaded files must
contain the contract's runtime EVM bytecode as a hex string (see
[`samples/`](samples/)). The CLI can also take Solidity source directly.

---

## Requirements

- **Python 3.8+** (tested on Ubuntu 20.04 LTS)
- **MongoDB** running locally at `mongodb://localhost:27017`
- For analysing Solidity **source** with the CLI: [`solc-select`](https://github.com/crytic/solc-select) / a matching `solc` binary (not needed for bytecode mode)

---

## Installation

```bash
git clone https://github.com/JustAbid/achecker-gui.git
cd achecker-gui

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Make sure a MongoDB instance is running before starting the web app:

```bash
# example (Ubuntu / systemd)
sudo systemctl start mongod
```

---

## Usage

### Web interface

```bash
python3 app.py
```

Then open <http://127.0.0.1:5000>, upload a bytecode file, and click **Analyze**.

### Command line

```bash
python3 bin/achecker.py -f samples/CVE-2021-34273.code -b -m 8
```

| Flag | Meaning |
|------|---------|
| `-f` | path to the contract file |
| `-b` | treat the input as EVM bytecode (omit for Solidity source) |
| `-m` | max memory in GB (default: 6) |
| `-sf` | save-file base name |

---

## Project structure

```
achecker-gui/
├── app.py               # Flask server: upload → analyze → results + history
├── bin/achecker.py      # AChecker CLI entry point
├── src/                 # AChecker static-analysis engine
│   ├── cfg/             # CFG recovery, disassembly, bundled Rattle (SSA)
│   ├── evm/             # symbolic EVM
│   ├── explorer/        # path exploration
│   ├── flow/            # data-flow / taint analysis and the detectors
│   └── util/            # helpers
├── templates/           # index.html, uploads.html
├── static/
│   ├── css/styles.css   # themes, buttons, loader
│   └── js/scripts.js    # theme toggle, loader handling
├── samples/             # example contract bytecode (incl. CVE-2021-34273)
├── uploads/             # runtime upload directory (git-ignored)
├── requirements.txt
└── setup.py
```

---

## Credits

The detection engine is **AChecker** by Asem Ghaleb, Julia Rubin, and Karthik
Pattabiraman (University of British Columbia), presented at ICSE 2023:

> A. Ghaleb, J. Rubin, and K. Pattabiraman, "AChecker: Statically Detecting
> Smart Contract Access Control Vulnerabilities," *2023 IEEE/ACM 45th
> International Conference on Software Engineering (ICSE)*, 2023.

```bibtex
@inproceedings{ghaleb2023achecker,
  title     = {AChecker: Statically Detecting Smart Contract Access Control Vulnerabilities},
  author    = {Ghaleb, Asem and Rubin, Julia and Pattabiraman, Karthik},
  booktitle = {2023 IEEE/ACM 45th International Conference on Software Engineering (ICSE)},
  year      = {2023},
  publisher = {IEEE}
}
```

Upstream repository: <https://github.com/DependableSystemsLab/AChecker>

Only the Flask app, templates, and static assets in this repository are my
addition.

---

## License

MIT — see [LICENSE](LICENSE). Bundled third-party components (Rattle, teEther)
retain their own licenses; details are in `LICENSE`.
