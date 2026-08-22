from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from cryptography.fernet import Fernet
import secrets

class Encryption:
    def __init__(self, key: bytes):
        self.__passwordHasher = PasswordHasher()
        self.__fernet = Fernet(key)
        
    def hashPassword(self, password: str) -> str:
        return self.__passwordHasher.hash(password)
    
    def verifyPassword(self, password: str, hashedPassword: str) -> bool:
        try:
            return self.__passwordHasher.verify(hashedPassword, password)
        except (VerifyMismatchError, VerificationError):
                    return False
        
    def encryptSecret(self, secret: str) -> str:
        return self.__fernet.encrypt(secret.encode()).decode()
        
    def decryptSecret(self, encryptedSecret: str) -> str:
        return self.__fernet.decrypt(encryptedSecret.encode()).decode()
    
    def generateSessionToken(self) -> str:
        return secrets.token_urlsafe(32)