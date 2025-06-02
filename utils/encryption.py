"""
Encryption utilities for secure credential storage
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.key_file = "data/encryption.key"
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Get existing encryption key or create a new one"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    return f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                self.logger.info("Generated new encryption key")
                return key
        except Exception as e:
            self.logger.error(f"Failed to handle encryption key: {e}")
            raise
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string data"""
        try:
            return self.fernet.encrypt(data.encode())
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data back to string"""
        try:
            return self.fernet.decrypt(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
