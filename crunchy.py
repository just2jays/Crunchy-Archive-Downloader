#!/usr/bin/env python3
"""
Crunchy Archive Downloader - Modern Python version
Automatically downloads the latest shows from Archive.org for specified artists.
"""

import argparse
import json
import logging
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Optional
import yaml

try:
    from internetarchive import search_items, download, get_item
except ImportError:
    print("Error: internetarchive library not found.")
    print("Please install it with: pip install internetarchive")
    sys.exit(1)


class CrunchyDownloader:
    """Downloads live music shows from Archive.org with duplicate detection."""
    
    def __init__(self, config_path: str, download_dir: str, max_shows: int = 5, 
                 max_workers: int = 4, dry_run: bool = False):
        """
        Initialize the downloader.
        
        Args:
            config_path: Path to YAML configuration file with artist collections
            download_dir: Base directory for downloads
            max_shows: Maximum number of shows to fetch per artist (default: 5)
            max_workers: Number of parallel downloads (default: 4)
            dry_run: If True, only simulate downloads without actually downloading
        """
        self.config_path = Path(config_path)
        self.download_dir = Path(download_dir).expanduser()
        self.max_shows = max_shows
        self.max_workers = max_workers
        self.dry_run = dry_run
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.collections = self.load_config()
        
        # Create download directory if it doesn't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup tracking file for downloaded shows
        script_dir = Path(__file__).parent
        log_dir = script_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        self.identifiers_file = log_dir / "downloaded_shows.json"
        
        self.logger.info(f"Initialized Crunchy Downloader")
        self.logger.info(f"Download directory: {self.download_dir}")
        self.logger.info(f"Max shows per artist: {self.max_shows}")
        self.logger.info(f"Parallel workers: {self.max_workers}")
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No files will be downloaded")
    
    def setup_logging(self):
        """Configure logging to both file and console."""
        # Place logs in the script's directory (repo root) instead of download dir
        script_dir = Path(__file__).parent
        log_dir = script_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"crunchy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Create logger
        self.logger = logging.getLogger('CrunchyDownloader')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def load_config(self) -> List[str]:
        """
        Load artist collections from YAML config file.
        
        Returns:
            List of collection identifiers
        """
        if not self.config_path.exists():
            self.logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            collections = config.get('collections', [])
            if not collections:
                self.logger.error("No collections found in configuration file")
                sys.exit(1)
            
            self.logger.info(f"Loaded {len(collections)} artist collections from config")
            return collections
        
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML configuration: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def get_existing_identifiers(self) -> Set[str]:
        """
        Load previously downloaded show identifiers from tracking file.
        
        Returns:
            Set of existing identifier strings
        """
        existing = set()
        
        if not self.identifiers_file.exists():
            self.logger.info("No tracking file found, starting fresh")
            return existing
        
        try:
            with open(self.identifiers_file, 'r') as f:
                data = json.load(f)
                # Extract identifiers from the tracking data
                for entry in data:
                    if isinstance(entry, dict) and 'identifier' in entry:
                        existing.add(entry['identifier'])
                    elif isinstance(entry, str):
                        # Support legacy format if needed
                        existing.add(entry)
            
            self.logger.info(f"Found {len(existing)} previously downloaded show identifiers")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error reading tracking file: {e}")
            self.logger.info("Starting with empty tracking file")
        except Exception as e:
            self.logger.error(f"Unexpected error loading tracking file: {e}")
        
        return existing
    
    def search_latest_shows(self, collection: str) -> List[Dict[str, str]]:
        """
        Search for the latest shows in a collection.
        
        Args:
            collection: Archive.org collection identifier
        
        Returns:
            List of dictionaries with 'identifier' and 'creator' keys
        """
        try:
            # Build search query
            query = f"collection:{collection}"
            
            # Search for items, sorted by addeddate descending
            results = []
            search_results = search_items(
                query,
                fields=['identifier', 'creator'],
                sorts=['addeddate desc'],
                params={'rows': self.max_shows}
            )
            
            count = 0
            for result in search_results:
                if count >= self.max_shows:
                    break
                
                identifier = result.get('identifier')
                creator = result.get('creator', collection)
                
                # Handle creator as list or string
                if isinstance(creator, list):
                    creator = creator[0] if creator else collection
                
                results.append({
                    'identifier': identifier,
                    'creator': self.sanitize_name(creator)
                })
                count += 1
            
            self.logger.info(f"Found {len(results)} shows for {collection}")
            return results
        
        except Exception as e:
            self.logger.error(f"Error searching collection {collection}: {e}")
            return []
    
    def sanitize_name(self, name: str) -> str:
        """
        Sanitize artist/creator name for use as directory name.
        
        Args:
            name: Raw name string
        
        Returns:
            Sanitized name safe for filesystem
        """
        # Replace spaces and special characters
        safe_name = name.replace(' ', '_')
        # Remove any characters that might cause issues
        safe_chars = []
        for char in safe_name:
            if char.isalnum() or char in ('_', '-'):
                safe_chars.append(char)
        
        return ''.join(safe_chars)
    
    def has_mp3_files(self, identifier: str) -> bool:
        """
        Check if an Archive.org item has any MP3 files.
        
        Args:
            identifier: Archive.org item identifier
        
        Returns:
            True if item has MP3 files, False otherwise
        """
        try:
            item = get_item(identifier)
            # Check if any files have .mp3 extension
            for file in item.files:
                if file.get('name', '').lower().endswith('.mp3'):
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"Could not check files for {identifier}: {e}")
            # If we can't check, assume it might have MP3s to avoid false negatives
            return True
    
    def save_downloaded_identifier(self, identifier: str, creator: str):
        """
        Save a downloaded show identifier to the tracking file.
        
        Args:
            identifier: Archive.org item identifier
            creator: Artist/creator name
        """
        try:
            # Load existing data
            data = []
            if self.identifiers_file.exists():
                with open(self.identifiers_file, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        self.logger.warning("Could not read existing tracking file, starting fresh")
                        data = []
            
            # Add new entry
            entry = {
                'identifier': identifier,
                'creator': creator,
                'downloaded_at': datetime.now().isoformat()
            }
            data.append(entry)
            
            # Save back to file
            with open(self.identifiers_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set proper permissions for the tracking file (rw-rw-r--)
            try:
                os.chmod(self.identifiers_file, 0o664)
            except Exception as perm_error:
                self.logger.warning(f"Could not set permissions for tracking file: {perm_error}")
            
            self.logger.debug(f"Saved identifier to tracking file: {identifier}")
        
        except Exception as e:
            self.logger.error(f"Error saving identifier to tracking file: {e}")
    
    def download_show(self, identifier: str, creator: str) -> bool:
        """
        Download a single show from Archive.org.
        
        Args:
            identifier: Archive.org item identifier
            creator: Artist/creator name for organizing downloads
        
        Returns:
            True if download successful, False otherwise
        """
        # Create artist directory
        artist_dir = self.download_dir / creator
        show_dir = artist_dir / identifier
        
        # Check if already exists
        if show_dir.exists():
            self.logger.info(f"Show already exists, skipping: {identifier}")
            return None
        
        # Check if item has MP3 files before proceeding
        if not self.has_mp3_files(identifier):
            self.logger.info(f"Show {identifier} has no MP3 files, skipping")
            return None
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would download: {identifier} to {show_dir}")
            return True
        
        try:
            # Create artist directory
            artist_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Downloading: {identifier}")
            
            # Download only VBR MP3 files
            download(
                identifier,
                destdir=str(artist_dir),
                glob_pattern='*.mp3',
                no_directory=False,
                retries=3,
                verbose=False,
            )
            
            # Verify download
            if show_dir.exists():
                # Count downloaded files
                mp3_files = list(show_dir.glob('*.mp3'))
                self.logger.info(f"Successfully downloaded {len(mp3_files)} MP3 files for {identifier}")
                
                # Set proper permissions so files can be modified later
                try:
                    # Set directory permissions to 775 (rwxrwxr-x)
                    os.chmod(show_dir, 0o775)
                    # Set file permissions to 664 (rw-rw-r--) for all downloaded files
                    for mp3_file in mp3_files:
                        os.chmod(mp3_file, 0o664)
                    self.logger.debug(f"Set permissions for {identifier}")
                except Exception as perm_error:
                    self.logger.warning(f"Could not set permissions for {identifier}: {perm_error}")
                
                # Save to tracking file
                self.save_downloaded_identifier(identifier, creator)
                
                return True
            else:
                self.logger.warning(f"Download completed but directory not found: {show_dir}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error downloading {identifier}: {e}")
            # Clean up partial download
            if show_dir.exists():
                try:
                    shutil.rmtree(show_dir)
                    self.logger.info(f"Cleaned up partial download: {show_dir}")
                except Exception as cleanup_error:
                    self.logger.error(f"Error cleaning up {show_dir}: {cleanup_error}")
            return False
    
    def run(self):
        """Main execution method."""
        self.logger.info("=" * 60)
        self.logger.info("Starting Crunchy Archive Downloader")
        self.logger.info("=" * 60)
        
        # Get existing identifiers to avoid duplicates
        existing_ids = self.get_existing_identifiers()
        
        # Collect all shows to download
        shows_to_download = []
        
        for collection in self.collections:
            self.logger.info(f"Processing collection: {collection}")
            shows = self.search_latest_shows(collection)
            
            for show in shows:
                identifier = show['identifier']
                creator = show['creator']
                
                # Check if already downloaded
                if identifier in existing_ids:
                    self.logger.debug(f"Skipping duplicate: {identifier}")
                    continue
                
                shows_to_download.append((identifier, creator))
        
        if not shows_to_download:
            self.logger.info("No new shows to download!")
            return
        
        self.logger.info(f"Found {len(shows_to_download)} new shows to download")
        
        # Download shows in parallel
        successful = 0
        failed = 0
        skipped = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_show = {
                executor.submit(self.download_show, identifier, creator): (identifier, creator)
                for identifier, creator in shows_to_download
            }
            
            # Process completed downloads
            for future in as_completed(future_to_show):
                identifier, creator = future_to_show[future]
                try:
                    result = future.result()
                    if result is True:
                        successful += 1
                    elif result is None:
                        skipped += 1
                    else:
                        failed += 1
                except Exception as e:
                    self.logger.error(f"Unexpected error for {identifier}: {e}")
                    failed += 1
        
        # Summary
        self.logger.info("=" * 60)
        self.logger.info(f"Download Summary:")
        self.logger.info(f"  Successful: {successful}")
        self.logger.info(f"  Skipped: {skipped}")
        self.logger.info(f"  Failed: {failed}")
        self.logger.info(f"  Total: {successful + skipped + failed}")
        self.logger.info("=" * 60)
        
        if failed > 0:
            self.logger.warning(f"{failed} downloads failed. Check logs for details.")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Automatically download latest live music shows from Archive.org',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Use default config and directory
  %(prog)s -c custom.yaml           # Use custom config file
  %(prog)s -d /mnt/music            # Use custom download directory
  %(prog)s -n 10 -w 8               # Download 10 shows per artist with 8 parallel workers
  %(prog)s --dry-run                # Preview what would be downloaded
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '-d', '--download-dir',
        default='~/Music/live-music',
        help='Base directory for downloads (default: ~/Music/live-music)'
    )
    
    parser.add_argument(
        '-n', '--max-shows',
        type=int,
        default=1,
        help='Maximum shows to download per artist (default: 1)'
    )
    
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=2,
        help='Number of parallel download workers (default: 2)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate downloads without actually downloading files'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        downloader = CrunchyDownloader(
            config_path=args.config,
            download_dir=args.download_dir,
            max_shows=args.max_shows,
            max_workers=args.workers,
            dry_run=args.dry_run
        )
        downloader.run()
    
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
