# OmniConverter Desktop

A macOS desktop app for converting documents between formats.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python3 app.py
```

## Features

- File picker — select multiple PDF, TXT, or HTML files
- Choose any output directory
- Convert to EPUB, PDF, or both at once
- Dark themed UI (Catppuccin Mocha)
- Threaded conversion — UI stays responsive
- Cancel button to stop mid-conversion

## Supported formats

| Input       | Output      |
|-------------|-------------|
| PDF (`.pdf`) | EPUB (`.epub`) |
| TXT (`.txt`) | PDF (`.pdf`)   |
| HTML (`.html`, `.htm`) | |

## Package as .app (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed app.py
```

The `.app` bundle will be in `dist/`.
