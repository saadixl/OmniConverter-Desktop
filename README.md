# OmniConverter Desktop

A macOS desktop app for converting documents between formats.

## Download

Grab the latest release from the [Releases page](https://github.com/saadixl/OmniConverter-Desktop/releases).

### Installation

1. Download `OmniConverter-macOS-arm64.zip` from the latest release
2. Unzip it
3. Move `OmniConverter.app` to your Applications folder

### macOS Gatekeeper notice

Since the app is not signed with an Apple Developer certificate, macOS will block it on first launch with a message like:

> Apple could not verify "OmniConverter" is free of malware

To open it, do **one** of the following:

**Option A** — Right-click to open:
1. Right-click (or Control-click) on `OmniConverter.app`
2. Click **Open**
3. Click **Open** again in the confirmation dialog

**Option B** — Remove the quarantine flag via Terminal:
```bash
xattr -cr /Applications/OmniConverter.app
```

After either step, the app will open normally from then on.

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

## Development

### Run from source

```bash
pip install -r requirements.txt
python3 app.py
```

### Build the .app bundle

```bash
pip install pyinstaller
python3 -m PyInstaller --noconfirm OmniConverter.spec
```

The `.app` bundle will be in `dist/`.
