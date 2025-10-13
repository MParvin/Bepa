# Beppa - Network Monitor

A simple network monitoring tool that watches your computer's connections & alerts you when your computer connects to specific IP addresses or networks.

It's useful to detect malicious connections to your private network.

Imagine one of your programs has malware that starts scanning your private network - with this simple script you can detect which process is making those connections.

## What it does

- Monitors all network connections from your computer
- Alerts you when connections are made to target IP ranges
- Shows desktop notifications when connections are detected
- Can exclude certain IP addresses from monitoring
- Runs continuously in the background

## Requirements

- Linux system (tested on Fedora)
- Python 3
- Root privileges (for full network monitoring, you can use without root privileges)

## Setup

1. Copy the example config file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to set your target IP ranges:
   ```bash
   nano .env
   ```

3. Install Python dependencies:
   ```bash
   pip install psutil python-dotenv
   ```

4. Install notification support:
   ```bash
   sudo dnf install libnotify  # For Fedora
   # or
   sudo apt install libnotify-bin  # For Ubuntu/Debian
   ```

## How to use

Run with root privileges:
```bash
sudo python3 main.py
```

Press `Ctrl+C` to stop monitoring.


## Notes

- Run as root for complete network visibility
- Lower monitor intervals use more CPU
- Notifications work on GNOME desktop environments
- The tool only monitors outgoing connections

## Todo

[ ] Systemd file

[ ] Installation script
