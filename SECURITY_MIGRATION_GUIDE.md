# Security Migration Guide

**Date:** 2026-03-14  
**Version:** 1.0 → 2.0 (Secure)

## Overview

This guide helps you migrate from the old authentication system to the new secure authentication system with enhanced security features.

## What's New in Secure Auth

### Security Enhancements

1. **✅ Encrypted Token Storage**
   - OAuth tokens are now encrypted at rest using Fernet (symmetric encryption)
   - Encryption key can be persisted in `.env` file

2. **✅ OAuth CSRF Protection**
   - State parameter validation prevents CSRF attacks
   - Cryptographically secure random state tokens

3. **✅ Security Audit Logging**
   - All authentication events logged to `logs/security_audit.log`
   - Tracks successful/failed auth attempts, token refreshes, CSRF attempts

4. **✅ Rate Limiting**
   - OAuth callback server has rate limiting (10 requests per 60 seconds per IP)
   - Prevents brute force and DoS attacks

5. **✅ Secure File Permissions**
   - Credentials directory created with 0o700 (owner only)
   - Credentials file set to 0o600 (owner read/write only)

6. **✅ Security Headers**
   - HTTP responses include security headers (X-Frame-Options, CSP, etc.)
   - Prevents XSS, clickjacking, and other attacks

## Migration Steps

### Step 1: Install New Dependencies

```bash
pip install cryptography>=41.0.0
```

Or update all dependencies:
```bash
pip install -r requirements.txt
```

### Step 2: Backup Existing Credentials (Optional)

If you have existing credentials you want to preserve:

```bash
# Backup old credentials
cp config/credentials.json config/credentials.json.backup
```

### Step 3: Generate Encryption Key (Optional)

To persist your encryption key across sessions:

```python
# Generate a new encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the output to your `.env` file:
```bash
TOKEN_ENCRYPTION_KEY=your_generated_key_here
```

**Note:** If you don't set this, a new key will be generated each time, and you'll need to re-authenticate.

### Step 4: Update Your Code

The new secure auth module is a drop-in replacement:

**Old Code:**
```python
from src.auth import StravaAuthenticator, get_authenticated_client

authenticator = StravaAuthenticator(
    client_id=client_id,
    client_secret=client_secret
)
```

**New Code:**
```python
from src.auth_secure import SecureStravaAuthenticator, get_authenticated_client

authenticator = SecureStravaAuthenticator(
    client_id=client_id,
    client_secret=client_secret
)
```

**Note:** `main.py` has already been updated to use the secure module.

### Step 5: Re-authenticate

After migration, you'll need to re-authenticate:

```bash
python3 main.py --auth
```

This will:
1. Generate a secure state token
2. Open your browser for OAuth authorization
3. Receive the callback with state validation
4. Encrypt and save tokens with secure permissions
5. Log all events to security audit log

### Step 6: Verify Security Features

Check that security features are working:

```bash
# 1. Verify encrypted credentials file
file config/credentials.json
# Should show: data (encrypted)

# 2. Check file permissions
ls -la config/credentials.json
# Should show: -rw------- (600)

# 3. Review security audit log
cat logs/security_audit.log
# Should show authentication events

# 4. Verify encryption key warning (if not set)
# You should see a warning about TOKEN_ENCRYPTION_KEY if not in .env
```

## Migrating Existing Tokens

If you want to migrate existing plaintext tokens to encrypted storage:

```python
#!/usr/bin/env python3
"""Migrate plaintext tokens to encrypted storage."""

import json
from pathlib import Path
from src.auth_secure import SecureTokenStorage

# Load old plaintext tokens
old_creds = Path('config/credentials.json.backup')
if old_creds.exists():
    with open(old_creds, 'r') as f:
        tokens = json.load(f)
    
    # Save with encryption
    storage = SecureTokenStorage('config/credentials.json')
    storage.save_tokens(tokens)
    
    print("✓ Tokens migrated to encrypted storage")
else:
    print("No backup file found. Please re-authenticate.")
```

Save as `migrate_tokens.py` and run:
```bash
python3 migrate_tokens.py
```

## Troubleshooting

### Issue: "Failed to load tokens"

**Cause:** Encryption key changed or tokens corrupted

**Solution:**
1. Delete `config/credentials.json`
2. Re-authenticate: `python3 main.py --auth`

### Issue: "Rate limit exceeded"

**Cause:** Too many requests to OAuth callback server

**Solution:**
- Wait 60 seconds and try again
- Check for malicious activity in `logs/security_audit.log`

### Issue: "Invalid state parameter (CSRF detected)"

**Cause:** State parameter mismatch (possible CSRF attack or browser issue)

**Solution:**
1. Close all browser windows
2. Clear browser cache
3. Try authentication again
4. Check `logs/security_audit.log` for details

### Issue: "TOKEN_ENCRYPTION_KEY warning on every run"

**Cause:** Encryption key not persisted in `.env`

**Solution:**
1. Generate key: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. Add to `.env`: `TOKEN_ENCRYPTION_KEY=your_key_here`
3. Re-authenticate to encrypt with persistent key

## Security Best Practices

### Do's ✅

- ✅ Set `TOKEN_ENCRYPTION_KEY` in `.env` for persistent encryption
- ✅ Keep `.env` file private (never commit to git)
- ✅ Review `logs/security_audit.log` regularly
- ✅ Rotate Strava API credentials if exposed
- ✅ Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- ✅ Set restrictive file permissions on sensitive files

### Don'ts ❌

- ❌ Don't share your encryption key
- ❌ Don't commit `.env` or `config/credentials.json` to git
- ❌ Don't ignore security warnings in logs
- ❌ Don't disable security features
- ❌ Don't use the old `auth.py` module (deprecated)

## Rollback (If Needed)

If you need to rollback to the old authentication system:

```python
# In main.py, change:
from src.auth_secure import SecureStravaAuthenticator
# Back to:
from src.auth import StravaAuthenticator
```

**Note:** This is NOT recommended as it removes all security enhancements.

## Comparison: Old vs New

| Feature | Old Auth | Secure Auth |
|---------|----------|-------------|
| Token Encryption | ❌ Plaintext | ✅ Encrypted (Fernet) |
| CSRF Protection | ❌ No | ✅ State parameter |
| Audit Logging | ❌ No | ✅ Full logging |
| Rate Limiting | ❌ No | ✅ 10 req/60s |
| File Permissions | ❌ Default | ✅ Restrictive (600) |
| Security Headers | ❌ No | ✅ Full headers |
| HTTPS Callback | ❌ HTTP only | ✅ Secure headers |

## Testing Your Migration

Run this checklist after migration:

```bash
# 1. Test authentication
python3 main.py --auth

# 2. Verify encrypted storage
python3 -c "
from src.auth_secure import SecureTokenStorage
storage = SecureTokenStorage('config/credentials.json')
tokens = storage.load_tokens()
print('✓ Tokens loaded successfully' if tokens else '✗ Failed to load tokens')
"

# 3. Check security log
tail -20 logs/security_audit.log

# 4. Verify file permissions
ls -la config/credentials.json logs/security_audit.log

# 5. Test token refresh
python3 main.py --fetch
```

## Support

If you encounter issues during migration:

1. Check `logs/security_audit.log` for detailed error messages
2. Review `SECURITY_RESOLUTION_PLAN.md` for security details
3. See `SECURITY.md` for security policy
4. Create an issue on GitHub with logs (redact sensitive info)

## Next Steps

After successful migration:

1. ✅ Review security audit logs regularly
2. ✅ Set up automated dependency updates
3. ✅ Consider implementing additional security measures from `SECURITY_RESOLUTION_PLAN.md`
4. ✅ Update your deployment documentation
5. ✅ Train team members on new security features

---

**Migration Complete!** 🎉

Your application now has enterprise-grade security for OAuth token management.

**Last Updated:** 2026-03-14