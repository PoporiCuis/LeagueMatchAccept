# LoL Match Assistant

A Python desktop companion for the League of Legends client. It can accept match queues, automate champion picks and bans, use role-specific champion profiles, and run from the system tray.

## Run from source

1. Install Python 3.10 or newer.
2. Open a terminal in this folder and install dependencies with `pip install -r requirements.txt`.
3. Run `python main.py`.
4. Launch the League client to enable client-connected features.

The app stores your settings in `config.json` and refreshes champion ownership from your running League client. Keep personal settings and generated ownership data out of commits.

## Build for Windows

Run `BUILD_RELEASE.bat` from this folder. It installs the listed dependencies and builds the Windows executable with PyInstaller.
