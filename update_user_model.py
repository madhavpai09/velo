#!/usr/bin/env python3
"""Update User model with OAuth support fields"""

with open('serverapp/database/models.py', 'r') as f:
    content = f.read()

old_user_class = '''# NEW: Application User Model (Riders)
class User(Base):
    """Authenticated user model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)'''

new_user_class = '''# NEW: Application User Model (Riders)
class User(Base):
    """Authenticated user model with OAuth support"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Made nullable for OAuth users
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # OAuth Support Fields
    auth_provider = Column(String, default="local")  # 'local', 'google', 'github'
    provider_id = Column(String, nullable=True)  # ID from OAuth provider
    last_login = Column(DateTime, nullable=True)  # Track last login time
    is_email_verified = Column(Boolean, default=False)  # Email verification status'''

if old_user_class in content:
    content = content.replace(old_user_class, new_user_class)
    with open('serverapp/database/models.py', 'w') as f:
        f.write(content)
    print("✅ Updated User model with OAuth support fields")
    print("   - auth_provider (local/google/github)")
    print("   - provider_id (OAuth provider user ID)")
    print("   - last_login (timestamp)")
    print("   - is_email_verified (boolean)")
    print("   - Made hashed_password nullable for OAuth users")
else:
    print("❌ Could not find User class to update")
