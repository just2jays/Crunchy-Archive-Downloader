# Crunchy Archive Downloader - AI Coding Guidelines

## Project Overview

Single-file Python CLI tool that downloads live music recordings from Archive.org using the `internetarchive` library. Originally a bash script, now a modern Python 3 class-based implementation with parallel downloads and duplicate detection.

**Core architecture**: `CrunchyDownloader` class orchestrates the entire workflow - config loading, archive search, duplicate detection, and parallel downloads.

## Key Design Patterns

### Duplicate Detection System
- Tracks downloaded shows in `logs/downloaded_shows.json` (repo-local, not in download dir)
- JSON entries: `{"identifier": "gd1977-05-08...", "creator": "GratefulDead", "downloaded_at": "2026-01-19T..."}`
- Checks both tracking file AND filesystem (shows already exist on disk)
- Archive.org identifiers are globally unique, used as folder names

### Logging Architecture
- **Critical**: Logs live in repo's `logs/` directory, NOT in download directory
- This separation exists because download dir may be on mounted drives or shared filesystems
- Per-run timestamped logs: `crunchy_YYYYMMDD_HHMMSS.log`
- Both file (DEBUG) and console (INFO) handlers

### File Organization
```
~/Music/live-music/          # Default download dir (configurable)
  GratefulDead/              # Sanitized creator name (spaces → underscores)
    gd1977-05-08.../         # Archive.org identifier (unique folder)
      track01.mp3
      track02.mp3
Crunchy-Archive-Downloader/  # Repo root
  logs/                      # All logs and tracking data here
    downloaded_shows.json
    crunchy_20260119_023000.log
```

## Critical Implementation Details

### Parallel Downloads with ThreadPoolExecutor
- Default 2 workers (conservative for bandwidth)
- Returns `True` (success), `False` (failed), or `None` (skipped)
- Failed downloads trigger cleanup via `shutil.rmtree()` of partial directories

### Archive.org API Usage
```python
# Search pattern - sorts by addeddate descending
search_items(query, fields=['identifier', 'creator'], 
             sorts=['addeddate desc'], params={'rows': max_shows})

# Download pattern - glob for MP3s only
download(identifier, destdir=artist_dir, glob_pattern='*.mp3', 
         no_directory=False, retries=3)
```

### File Permissions Pattern
- Directories: `0o777` (rwxrwxrwx) - world writable for remote access (sshfs)
- MP3 files: `0o666` (rw-rw-rw-) - world writable for remote editing (MusicBrainz Picard via sshfs)
- Tracking file: `0o664` 
- Permission setting wrapped in try/except (may fail on NTFS/FAT mounts)

### Creator Name Sanitization
- Spaces → underscores
- Only alphanumeric, `_`, and `-` allowed
- Used for directory names: `Phish` → `Phish`, `Umphreys McGee` → `Umphreys_McGee`

## Testing Approach

Run with pytest: `python3 -m pytest test_crunchy.py -v`

Tests use:
- `tempfile.mkdtemp()` for isolated test directories
- Fixtures for config files and temp dirs
- Mock objects for Archive.org API (avoid network calls)

Add tests for new features in [test_crunchy.py](test_crunchy.py) following existing fixture patterns.

## Configuration

YAML structure in [config.yaml](config.yaml):
```yaml
collections:
  - GratefulDead  # Archive.org collection identifier
  - Phish         # Not all Archive.org collections work
```

**Important**: Collection names must exactly match Archive.org collection identifiers. User can comment out (`#`) collections to skip.

## Common Modifications

**Adding new CLI options**: Update `argparse` in `main()`, pass through `CrunchyDownloader.__init__()`, and use in relevant methods.

**Changing download filters**: Modify `download()` call's `glob_pattern` parameter (currently `*.mp3`). Also update `has_mp3_files()` check to match.

**New tracking fields**: Add to `save_downloaded_identifier()` method's entry dict. Backward compatible - handles legacy string format.

## Cron Integration

Designed for unattended execution:
- All output goes to logs (no stdin required)
- Paths use `Path().expanduser()` for `~` expansion
- Exit codes: 0 (success), 1 (failure/interrupt)
- Example: `0 2 * * * cd /path/to/repo && python3 crunchy.py >> /tmp/crunchy.log 2>&1`

## Common Pitfalls

1. **Don't put logs in download directory** - breaks on network mounts
2. **Archive.org API can be slow** - don't increase workers too aggressively (rate limiting)
3. **Empty downloads return success** - items without MP3s "download" successfully but create no directory. Use `has_mp3_files()` pre-check to avoid.
4. **Creator field can be list or string** - always check type before use
5. **Permissions may fail silently** - always wrap `os.chmod()` in try/except

## External Dependencies

- `internetarchive>=5.5.1` - Archive.org API client (critical)
- `PyYAML>=6.0` - Config file parsing
- `pytest>=7.0.0` - Testing only

No database, no web framework, no external services beyond Archive.org.
