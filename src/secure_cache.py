"""
Secure cache storage with encryption for PII protection.

Implements encrypted caching to protect sensitive data like GPS coordinates,
activity details, and location information.

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.
"""

import json
import logging
import os
import hashlib
import hmac
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class SecureCacheStorage:
    """Handles encrypted storage of cache files containing PII."""
    
    def __init__(self, cache_path: str, encryption_key: Optional[bytes] = None):
        """
        Initialize secure cache storage.
        
        Args:
            cache_path: Path to cache file
            encryption_key: Optional encryption key (will be generated if not provided)
        """
        self.cache_path = Path(cache_path)
        
        # Get or generate encryption key
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            key = self._get_or_create_key()
            self.cipher = Fernet(key)
    
    def _get_or_create_key(self) -> bytes:
        """
        Get existing encryption key or create new one with persistence.
        
        Returns:
            Encryption key bytes
        """
        key_file = Path('config/.cache_encryption_key')
        
        # Check environment variable first
        env_key = os.getenv('CACHE_ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()
        
        # Check for existing key file
        if key_file.exists():
            try:
                key = key_file.read_bytes()
                logger.info("✓ Loaded existing cache encryption key")
                return key
            except Exception as e:
                logger.warning(f"Failed to load encryption key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save key with secure permissions
        try:
            key_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            key_file.write_bytes(key)
            os.chmod(key_file, 0o600)
            
            logger.warning("=" * 70)
            logger.warning("GENERATED NEW CACHE ENCRYPTION KEY")
            logger.warning("=" * 70)
            logger.warning(f"Key saved to: {key_file}")
            logger.warning("To use across systems, add to .env:")
            logger.warning(f"CACHE_ENCRYPTION_KEY={key.decode()}")
            logger.warning("=" * 70)
        except Exception as e:
            logger.error(f"Failed to save encryption key: {e}")
        
        return key
    
    def _calculate_hmac(self, data: bytes) -> bytes:
        """
        Calculate HMAC for data integrity verification.
        
        Args:
            data: Data to calculate HMAC for
            
        Returns:
            HMAC bytes
        """
        # Use encryption key as HMAC key
        key = self.cipher._signing_key  # Access internal key
        return hmac.new(key, data, hashlib.sha256).digest()
    
    def save_cache(self, data: Dict[str, Any]) -> None:
        """
        Save cache data with encryption and integrity protection.
        
        Args:
            data: Dictionary to cache
        """
        try:
            # Add metadata
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            # Serialize to JSON
            json_data = json.dumps(cache_data)
            
            # Encrypt
            encrypted = self.cipher.encrypt(json_data.encode())
            
            # Calculate HMAC for integrity
            mac = self._calculate_hmac(encrypted)
            
            # Combine MAC + encrypted data
            protected_data = mac + encrypted
            
            # Create directory with restrictive permissions
            self.cache_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            # Write encrypted data
            self.cache_path.write_bytes(protected_data)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.cache_path, 0o600)
            
            logger.info(f"✓ Cache saved securely to {self.cache_path}")
            
        except Exception as e:
            logger.error(f"Failed to save secure cache: {e}")
            raise
    
    def load_cache(self) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt cache data with integrity verification.
        
        Returns:
            Cached dictionary or None if file doesn't exist or is invalid
        """
        if not self.cache_path.exists():
            return None
        
        try:
            # Read protected data
            protected_data = self.cache_path.read_bytes()
            
            # Split MAC and encrypted data
            mac = protected_data[:32]  # SHA256 produces 32 bytes
            encrypted = protected_data[32:]
            
            # Verify integrity
            expected_mac = self._calculate_hmac(encrypted)
            if not hmac.compare_digest(mac, expected_mac):
                logger.error("Cache integrity check failed - data may be tampered")
                return None
            
            # Decrypt
            decrypted = self.cipher.decrypt(encrypted)
            cache_data = json.loads(decrypted.decode())
            
            logger.info(f"✓ Cache loaded from {self.cache_path}")
            logger.info(f"  Cache timestamp: {cache_data.get('timestamp')}")
            
            return cache_data.get('data')
            
        except Exception as e:
            logger.error(f"Failed to load secure cache: {e}")
            return None
    
    def delete_cache(self) -> None:
        """Delete cache file securely."""
        if self.cache_path.exists():
            try:
                # Overwrite with random data before deletion (secure delete)
                file_size = self.cache_path.stat().st_size
                self.cache_path.write_bytes(os.urandom(file_size))
                self.cache_path.unlink()
                logger.info(f"✓ Cache deleted securely: {self.cache_path}")
            except Exception as e:
                logger.error(f"Failed to delete cache: {e}")


def migrate_cache_to_encrypted(old_cache_path: str, new_cache_path: str) -> bool:
    """
    Migrate existing plaintext cache to encrypted format.
    
    Args:
        old_cache_path: Path to existing plaintext cache
        new_cache_path: Path for new encrypted cache
        
    Returns:
        True if migration successful, False otherwise
    """
    old_path = Path(old_cache_path)
    
    if not old_path.exists():
        logger.info("No existing cache to migrate")
        return True
    
    try:
        # Load old cache
        with open(old_path, 'r') as f:
            old_data = json.load(f)
        
        # Save to encrypted cache
        secure_cache = SecureCacheStorage(new_cache_path)
        secure_cache.save_cache(old_data)
        
        # Securely delete old cache
        file_size = old_path.stat().st_size
        old_path.write_bytes(os.urandom(file_size))
        old_path.unlink()
        
        logger.info(f"✓ Migrated cache from {old_cache_path} to encrypted format")
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate cache: {e}")
        return False


# Made with Bob - Security Enhanced Edition