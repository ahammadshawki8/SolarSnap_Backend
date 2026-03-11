#!/usr/bin/env python3
"""
Generate secure keys for production deployment
"""
import secrets
import string

def generate_secret_key(length=32):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_key(length=64):
    """Generate a secure JWT key"""
    return secrets.token_urlsafe(length)

def main():
    """Generate and display secure keys"""
    print("🔐 SolarSnap Backend - Secure Key Generator")
    print("=" * 50)
    
    secret_key = generate_secret_key()
    jwt_key = generate_jwt_key()
    
    print("Copy these values to your production environment:")
    print()
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_key}")
    print()
    print("⚠️  Keep these keys secure and never commit them to version control!")
    print("💡 Use different keys for each environment (dev, staging, production)")

if __name__ == '__main__':
    main()