# Crunchy-Archive-Downloader

A modern Python script for automatically downloading the latest live music recordings from Archive.org. Originally written as a bash script over a decade ago, now modernized with Python 3 for better performance, reliability, and maintainability.

## Features

- 🎵 **Automatic Downloads**: Fetches the latest shows from your favorite artists
- 🔍 **Smart Duplicate Detection**: Uses show identifiers to avoid re-downloading existing content
- 🚀 **Parallel Downloads**: Multi-threaded downloads for better performance
- 📝 **Detailed Logging**: Comprehensive logs of all operations
- ⚙️ **Configurable**: Easy YAML configuration for managing artist collections
- 🛡️ **Error Handling**: Robust error handling with automatic cleanup of failed downloads
- 💾 **Space Efficient**: Only downloads MP3 files, skips duplicates
- 🔄 **Cron-Friendly**: Designed to run on a schedule without manual intervention

## Requirements

- Python 3.8 or higher
- Internet connection
- Sufficient disk space for downloads

## Installation

1. Clone the repository:
```bash
git clone https://github.com/just2jays/Crunchy-Archive-Downloader.git
cd Crunchy-Archive-Downloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install internetarchive PyYAML
```

3. Make the script executable (optional):
```bash
chmod +x crunchy.py
```

## Configuration

Edit `config.yaml` to add or remove artist collections:

```yaml
collections:
  - GratefulDead
  - Phish
  - UmphreysMcGee
  # Add more collections here
```

Each collection name should match the Archive.org collection identifier.

## Usage

### Basic Usage

Run with default settings (downloads to `~/Music/live-music`):
```bash
python3 crunchy.py
```

### Custom Configuration

Specify a custom config file:
```bash
python3 crunchy.py -c my_config.yaml
```

Specify a custom download directory:
```bash
python3 crunchy.py -d /path/to/music/folder
```

Download more shows per artist:
```bash
python3 crunchy.py -n 10
```

Use more parallel workers for faster downloads:
```bash
python3 crunchy.py -w 8
```

### Dry Run

Preview what would be downloaded without actually downloading:
```bash
python3 crunchy.py --dry-run
```

### Combined Options

```bash
python3 crunchy.py -c config.yaml -d /mnt/music -n 10 -w 8
```

## Running on a Schedule (Cron)

To automatically download new shows daily, add a cron job:

1. Open your crontab:
```bash
crontab -e
```

2. Add a line to run daily at 2 AM (adjust path as needed):
```cron
0 2 * * * cd /path/to/Crunchy-Archive-Downloader && /usr/bin/python3 crunchy.py >> /tmp/crunchy.log 2>&1
```

Or weekly on Sundays at 3 AM:
```cron
0 3 * * 0 cd /path/to/Crunchy-Archive-Downloader && /usr/bin/python3 crunchy.py
```

## Directory Structure

Downloaded shows are organized by artist and identifier:
```
~/Music/live-music/
├── GratefulDead/
│   ├── gd1977-05-08.sbd.miller.97766.sbeok.flac16/
│   │   ├── song1.mp3
│   │   ├── song2.mp3
│   │   └── ...
│   └── gd1978-04-16.sbd.warner.0002.sbefail.shnf/
│       └── ...
├── UmphreysMcGee/
│   └── ...
└── logs/
    ├── crunchy_20260119_023000.log
    └── ...
```

## Command Line Options

```
usage: crunchy.py [-h] [-c CONFIG] [-d DOWNLOAD_DIR] [-n MAX_SHOWS] 
                  [-w WORKERS] [--dry-run] [-v]

Options:
  -h, --help            Show help message and exit
  -c, --config CONFIG   Path to configuration file (default: config.yaml)
  -d, --download-dir    Base directory for downloads (default: ~/Music/live-music)
  -n, --max-shows       Maximum shows to download per artist (default: 5)
  -w, --workers         Number of parallel download workers (default: 4)
  --dry-run             Simulate downloads without actually downloading
  -v, --verbose         Enable verbose output
```

## Duplicate Detection

The script uses a smart duplicate detection system:

1. Scans the download directory for existing show identifiers
2. Only downloads shows that don't already exist
3. Uses Archive.org's unique identifiers for reliable detection
4. Prevents wasting bandwidth and disk space

## Logging

Logs are automatically saved to `<download_dir>/logs/` with timestamps. Each run creates a new log file containing:
- Shows discovered and downloaded
- Errors and warnings
- Download statistics
- Performance metrics

## Migration from Old Bash Script

If you're migrating from the old `crunchy.sh` script:

1. Your existing downloads in `~/Music/live-music/` will be recognized
2. The directory structure remains compatible
3. The script will not re-download shows you already have
4. You can safely run the new script alongside the old one

## Updating Metadata and Tagging

The script currently focuses on downloading MP3 files. Metadata tagging is not implemented yet but may be added in future releases.

For now, you can use external tools like `beets` or `MusicBrainz Picard` to tag your downloaded files after the download process.

The best process for this is to first use `sshfs` to mount the remote directory locally, then run your tagging tool on the mounted directory.

**For example**:
`sshfs jj@192.168.1.205:/mnt/ssd/music ~/Music/PiMusic -o local,reconnect,noappledouble`

That command will mount the remote `/music/..` directory to your local `~/Music/PiMusic` folder, allowing your tagging tool to access the files as if they were local.


## Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'internetarchive'`
- **Solution**: Install dependencies with `pip install -r requirements.txt`

**Problem**: Downloads are slow
- **Solution**: Increase parallel workers with `-w 8` or higher

**Problem**: Running out of disk space
- **Solution**: Reduce max shows with `-n 3` or clean up old downloads

**Problem**: Some shows fail to download
- **Solution**: Check the log files in `<download_dir>/logs/` for details

**Problem**: Download completed but directory not found
- **Most likely cause**: The item might not have any MP3 files matching the *.mp3 glob pattern. The Archive.org library completes "successfully" (no exception) but creates no directory since there's nothing to download.


## Contributing

Feel free to submit issues or pull requests to improve the downloader!

## License

See LICENSE file for details.

## Credits

- Original bash script by just2jays
- Modernized Python version (2026)
- Uses the [Internet Archive Python Library](https://github.com/jjjake/internetarchive)
