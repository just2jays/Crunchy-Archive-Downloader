# Quick Start Guide

## Installation (One-time setup)

```bash
# Clone the repository
git clone https://github.com/just2jays/Crunchy-Archive-Downloader.git
cd Crunchy-Archive-Downloader

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

```bash
# Download latest 5 shows per artist (default)
python3 crunchy.py

# Preview what would be downloaded (dry run)
python3 crunchy.py --dry-run

# Download more shows per artist
python3 crunchy.py -n 10

# Use custom download location
python3 crunchy.py -d /path/to/music

# Faster downloads with more parallel workers
python3 crunchy.py -w 8
```

## Configuration

Edit `config.yaml` to customize which artists to download:

```yaml
collections:
  - GratefulDead
  - Phish
  - UmphreysMcGee
  # Add more here...
```

## Cron Setup (Automatic Downloads)

Run daily at 2 AM:
```bash
crontab -e
# Add this line:
0 2 * * * cd /path/to/Crunchy-Archive-Downloader && python3 crunchy.py
```

Run weekly on Sundays at 3 AM:
```bash
0 3 * * 0 cd /path/to/Crunchy-Archive-Downloader && python3 crunchy.py
```

## Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'internetarchive'`
```bash
pip install -r requirements.txt
```

**Problem**: Downloads are slow
```bash
python3 crunchy.py -w 8  # Use 8 parallel workers
```

**Problem**: Need to see what happened
```bash
# Check logs in:
~/Music/live-music/logs/crunchy_YYYYMMDD_HHMMSS.log
```

## File Locations

- **Downloads**: `~/Music/live-music/` (customizable with `-d`)
- **Logs**: `~/Music/live-music/logs/`
- **Config**: `config.yaml` in the script directory

## Key Features

✅ **Automatic duplicate detection** - Won't re-download existing shows  
✅ **Parallel downloads** - Fast multi-threaded downloads  
✅ **Error recovery** - Automatic retry and cleanup  
✅ **Detailed logging** - Track all operations  
✅ **Safe for cron** - Runs unattended without issues  

## More Help

- Full documentation: See [README.md](README.md)
- Migration guide: See [MIGRATION.md](MIGRATION.md)
- Get all options: `python3 crunchy.py --help`
