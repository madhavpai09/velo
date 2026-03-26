"""
Password validation and security utilities
"""
import re
from pydantic import BaseModel, validator
from typing import Optional


class PasswordValidator:
    """Validate password strength"""
    
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_NUMBER = True
    REQUIRE_SPECIAL = True
    
    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """
        Validate password strength
        Returns: (is_valid, error_message)
        """
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long"
        
        if PasswordValidator.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if PasswordValidator.REQUIRE_NUMBER and not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        if PasswordValidator.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",./<>?]', password):
            return False, "Password must contain at least one special character (!@#$%^&* etc.)"
        
        return True, ""
    
    @staticmethod
    def get_strength_score(password: str) -> int:
        """Get password strength score (0-100)"""
        score = 0
        
        # Length score
        score += min(len(password) * 5, 25)
        
        # Complexity score
        if re.search(r'[a-z]', password):
            score += 15
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'[0-9]', password):
            score += 15
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",./<>?]', password):
            score += 15
        
        # Character variety
        if re.search(r'[a-z].*[A-Z]|[A-Z].*[a-z]', password):
            score += 5
        
        return min(score, 100)
    
    @staticmethod
    def get_feedback(password: str) -> list[str]:
        """Get feedback on password to improve it"""
        feedback = []
        
        if len(password) < PasswordValidator.MIN_LENGTH:
            feedback.append(f"Add {PasswordValidator.MIN_LENGTH - len(password)} more characters")
        
        if not re.search(r'[A-Z]', password):
            feedback.append("Add at least one uppercase letter")
        
        if not re.search(r'[0-9]', password):
            feedback.append("Add at least one number")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",./<>?]', password):
            feedback.append("Add at least one special character")
        
        return feedback


class SecurePassword(str):
    """Password field with automatic strength validation"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        
        is_valid, error_msg = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error_msg)
        
        return v
