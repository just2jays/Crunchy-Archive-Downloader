#!/usr/bin/env python3
"""
Unit tests for Crunchy Archive Downloader
Run with: python3 -m pytest test_crunchy.py -v
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import yaml

# Import the CrunchyDownloader class
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the internetarchive module for testing
class MockSearchResult:
    def __init__(self, identifier, creator):
        self.data = {'identifier': identifier, 'creator': creator}
    
    def get(self, key, default=None):
        return self.data.get(key, default)

# Create a basic test configuration
TEST_CONFIG = {
    'collections': ['TestBand1', 'TestBand2']
}


class TestCrunchyDownloader:
    """Test cases for CrunchyDownloader class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def config_file(self, temp_dir):
        """Create a temporary config file"""
        config_path = Path(temp_dir) / 'test_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(TEST_CONFIG, f)
        return str(config_path)
    
    def test_sanitize_name(self):
        """Test name sanitization for filesystem safety"""
        # Import here to avoid issues if internetarchive is not installed
        try:
            from crunchy import CrunchyDownloader
        except ImportError:
            pytest.skip("internetarchive module not installed")
        
        # Create a temporary config for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(TEST_CONFIG, f)
            config_path = f.name
        
        try:
            dl = CrunchyDownloader(config_path, '/tmp/test', dry_run=True)
            
            # Test various name formats
            assert dl.sanitize_name("Grateful Dead") == "Grateful_Dead"
            assert dl.sanitize_name("String Cheese Incident") == "String_Cheese_Incident"
            assert dl.sanitize_name("Umphrey's McGee") == "Umphreys_McGee"
            assert dl.sanitize_name("moe.") == "moe"
            assert dl.sanitize_name("Test-Band-123") == "Test-Band-123"
        finally:
            os.unlink(config_path)
    
    def test_get_existing_identifiers(self, temp_dir, config_file):
        """Test detection of existing show identifiers"""
        try:
            from crunchy import CrunchyDownloader
        except ImportError:
            pytest.skip("internetarchive module not installed")
        
        download_dir = Path(temp_dir) / 'downloads'
        
        # Create mock directory structure
        (download_dir / 'GratefulDead' / 'gd1977-05-08').mkdir(parents=True)
        (download_dir / 'GratefulDead' / 'gd1978-04-16').mkdir(parents=True)
        (download_dir / 'Phish' / 'phish2023-07-14').mkdir(parents=True)
        
        dl = CrunchyDownloader(config_file, str(download_dir), dry_run=True)
        existing = dl.get_existing_identifiers()
        
        assert len(existing) == 3
        assert 'gd1977-05-08' in existing
        assert 'gd1978-04-16' in existing
        assert 'phish2023-07-14' in existing
    
    def test_config_loading(self, config_file):
        """Test configuration file loading"""
        try:
            from crunchy import CrunchyDownloader
        except ImportError:
            pytest.skip("internetarchive module not installed")
        
        dl = CrunchyDownloader(config_file, '/tmp/test', dry_run=True)
        
        assert len(dl.collections) == 2
        assert 'TestBand1' in dl.collections
        assert 'TestBand2' in dl.collections
    
    def test_invalid_config(self, temp_dir):
        """Test handling of invalid configuration"""
        try:
            from crunchy import CrunchyDownloader
        except ImportError:
            pytest.skip("internetarchive module not installed")
        
        # Test with non-existent config file
        with pytest.raises(SystemExit):
            CrunchyDownloader('/nonexistent/config.yaml', '/tmp/test', dry_run=True)
    
    def test_empty_collections(self, temp_dir):
        """Test handling of empty collections in config"""
        try:
            from crunchy import CrunchyDownloader
        except ImportError:
            pytest.skip("internetarchive module not installed")
        
        config_path = Path(temp_dir) / 'empty_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump({'collections': []}, f)
        
        with pytest.raises(SystemExit):
            CrunchyDownloader(str(config_path), '/tmp/test', dry_run=True)


def test_config_yaml_format():
    """Test that the default config.yaml is valid"""
    config_path = Path(__file__).parent / 'config.yaml'
    
    if not config_path.exists():
        pytest.skip("config.yaml not found")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    assert 'collections' in config
    assert isinstance(config['collections'], list)
    assert len(config['collections']) > 0


def test_requirements_txt_exists():
    """Test that requirements.txt exists and contains necessary packages"""
    req_path = Path(__file__).parent / 'requirements.txt'
    
    assert req_path.exists(), "requirements.txt not found"
    
    with open(req_path) as f:
        content = f.read()
    
    assert 'internetarchive' in content
    assert 'PyYAML' in content or 'pyyaml' in content.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
