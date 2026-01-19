# Migration Guide: From Bash to Python

This guide helps you transition from the old `crunchy.sh` bash script to the new `crunchy.py` Python implementation.

## Why Migrate?

The new Python implementation offers several advantages:

- **Better Performance**: Parallel downloads with configurable workers
- **Smart Duplicate Detection**: Uses Archive.org identifiers to prevent re-downloads
- **Error Handling**: Automatic retry logic and cleanup of failed downloads
- **Logging**: Detailed logs of all operations for troubleshooting
- **Maintainability**: Easier to extend and customize
- **Modern API**: Uses official Internet Archive Python library
- **Configuration**: YAML-based config instead of hardcoded band lists

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run with Default Settings**
   ```bash
   python3 crunchy.py
   ```
   
   Or use the wrapper script:
   ```bash
   ./run.sh
   ```

## Differences from Old Script

### Directory Structure
Both scripts use the same directory structure, so your existing downloads are compatible:
```
~/Music/live-music/
├── ArtistName/
│   └── show-identifier/
│       ├── track1.mp3
│       └── track2.mp3
```

### Configuration
**Old (bash)**: Band list hardcoded in script
```bash
band_collections << EOF
GratefulDead
Phish
EOF
```

**New (Python)**: YAML configuration file
```yaml
collections:
  - GratefulDead
  - Phish
```

### Duplicate Detection
**Old (bash)**: Checks if directory exists
```bash
if [ ! -d $DL_DIR$creator/$identifier ]; then
```

**New (Python)**: Scans all subdirectories for identifiers
```python
existing_ids = self.get_existing_identifiers()
```

The new method is more robust and will detect existing downloads even if directories were moved.

### Download Format
**Old (bash)**: Downloaded ZIP files and extracted them
```bash
wget $zip_url
unzip $ident.zip
```

**New (Python)**: Directly downloads MP3 files
```python
download(identifier, glob_pattern='*.mp3')
```

This saves disk space by not keeping ZIP files.

## Migration Steps

### Step 1: Verify Python Installation
```bash
python3 --version  # Should be 3.8 or higher
```

### Step 2: Install Dependencies
```bash
cd /path/to/Crunchy-Archive-Downloader
pip install -r requirements.txt
```

### Step 3: Create Configuration File
Edit `config.yaml` with your artist collections:
```bash
cp config.example.yaml config.yaml
nano config.yaml  # or use your preferred editor
```

### Step 4: Test with Dry Run
Preview what would be downloaded:
```bash
python3 crunchy.py --dry-run
```

### Step 5: Run First Download
```bash
python3 crunchy.py
```

### Step 6: Update Cron Job
**Old cron entry:**
```cron
0 2 * * * cd /path/to/script && bash crunchy.sh
```

**New cron entry:**
```cron
0 2 * * * cd /path/to/Crunchy-Archive-Downloader && python3 crunchy.py
```

Or using the wrapper:
```cron
0 2 * * * cd /path/to/Crunchy-Archive-Downloader && ./run.sh
```

## Advanced Configuration

### Custom Download Directory
```bash
python3 crunchy.py -d /mnt/external/music
```

### More Shows Per Artist
```bash
python3 crunchy.py -n 10
```

### Faster Downloads (More Parallel Workers)
```bash
python3 crunchy.py -w 8
```

### Combined Options
```bash
python3 crunchy.py -d /mnt/music -n 10 -w 8
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'internetarchive'"
Install dependencies:
```bash
pip install internetarchive PyYAML
```

### Cron Job Not Running
1. Check cron logs: `grep CRON /var/log/syslog`
2. Make sure paths are absolute in crontab
3. Add output redirection for debugging:
   ```cron
   0 2 * * * cd /full/path && python3 crunchy.py >> /tmp/crunchy.log 2>&1
   ```

### Downloads Are Slow
Increase parallel workers:
```bash
python3 crunchy.py -w 8
```

### Want to Keep Old Script
Both scripts can coexist. The new script will recognize downloads made by the old script and won't re-download them.

## FAQ

**Q: Will I lose my existing downloads?**
A: No, the new script uses the same directory structure and will recognize existing downloads.

**Q: Can I still use the bash script?**
A: Yes, but the Python version is recommended for better performance and reliability.

**Q: How do I add more artists?**
A: Edit `config.yaml` and add collection identifiers under the `collections:` section.

**Q: Where are the logs?**
A: Logs are saved in `<download-dir>/logs/` with timestamps.

**Q: Can I download more than 5 shows per artist?**
A: Yes, use the `-n` option: `python3 crunchy.py -n 10`

**Q: What if a download fails?**
A: The script automatically retries and cleans up partial downloads. Check the logs for details.

## Getting Help

If you encounter issues:
1. Check the logs in `~/Music/live-music/logs/`
2. Run with `--dry-run` to see what would happen
3. Open an issue on GitHub with the error message and log file

## Rollback Plan

If you need to revert to the old bash script:
1. Keep `crunchy.sh` in the repository (it's not deleted)
2. Update your cron job back to use `crunchy.sh`
3. The directory structure remains compatible
