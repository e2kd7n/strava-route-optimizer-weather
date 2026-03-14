# Security Resolution Plan

**Date:** 2026-03-14  
**Status:** 🚨 CRITICAL ISSUES FOUND - IMMEDIATE ACTION REQUIRED

## Executive Summary

A security audit of the codebase has identified **CRITICAL** security vulnerabilities that must be addressed immediately. The most severe issue is **exposed API credentials in the repository**, which poses an immediate security risk.

---

## 🚨 CRITICAL FINDINGS (Priority: IMMEDIATE)

### 1. **EXPOSED STRAVA API CREDENTIALS IN REPOSITORY**

**Severity:** 🔴 CRITICAL  
**File:** `.env`  
**Issue:** Hardcoded Strava API credentials are committed to the repository

**Current State:**
```
STRAVA_CLIENT_ID=210778
STRAVA_CLIENT_SECRET=6fd33aec16df44cc52ef7f0e83df1c920e8e04a3
```

**Risk:**
- ✗ API credentials are publicly visible if repository is public
- ✗ Credentials can be used to impersonate the application
- ✗ Potential for API abuse and rate limit exhaustion
- ✗ Violation of Strava API Terms of Service
- ✗ Git history contains these credentials permanently

**Impact:**
- Unauthorized access to Strava API using your credentials
- Potential account suspension by Strava
- Data breach if credentials are harvested
- Reputational damage

**Resolution Steps:**

1. **IMMEDIATE: Revoke Compromised Credentials**
   ```bash
   # Go to https://www.strava.com/settings/api
   # Delete the current application
   # Create a new application with new credentials
   ```

2. **Remove Credentials from Git History**
   ```bash
   # WARNING: This rewrites git history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Or use BFG Repo-Cleaner (recommended)
   bfg --delete-files .env
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

3. **Force Push to Remote (if applicable)**
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```

4. **Create .env.example Template**
   ```bash
   # Create template without real credentials
   cat > .env.example << 'EOF'
   # Strava API Credentials
   # Get these from https://www.strava.com/settings/api
   STRAVA_CLIENT_ID=your_client_id_here
   STRAVA_CLIENT_SECRET=your_client_secret_here
   EOF
   ```

5. **Update .gitignore (Already Done)**
   - ✓ `.env` is already in .gitignore
   - Ensure it stays there

6. **Document in README**
   - Add security notice about credentials
   - Reference .env.example for setup

**Status:** ⏳ PENDING - Requires immediate action

---

## 🔴 HIGH PRIORITY FINDINGS

### 2. **Unencrypted Token Storage**

**Severity:** 🔴 HIGH  
**File:** `src/auth.py` (lines 172-184)  
**Issue:** OAuth tokens stored in plaintext JSON file

**Current Implementation:**
```python
def save_tokens(self, tokens: Dict[str, any]) -> None:
    with open(self.credentials_path, 'w') as f:
        json.dump(tokens, f, indent=2)  # ❌ Plaintext storage
```

**Risk:**
- Access tokens stored without encryption
- Refresh tokens exposed on filesystem
- Anyone with file access can steal tokens

**Resolution:**
```python
import json
from cryptography.fernet import Fernet
import os

class SecureTokenStorage:
    def __init__(self, credentials_path: str):
        self.credentials_path = Path(credentials_path)
        # Get encryption key from environment or generate
        key = os.getenv('TOKEN_ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            logger.warning("Generated new encryption key. Set TOKEN_ENCRYPTION_KEY in .env")
        self.cipher = Fernet(key if isinstance(key, bytes) else key.encode())
    
    def save_tokens(self, tokens: Dict[str, any]) -> None:
        """Save tokens with encryption."""
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Encrypt token data
        token_json = json.dumps(tokens)
        encrypted = self.cipher.encrypt(token_json.encode())
        
        # Write encrypted data
        with open(self.credentials_path, 'wb') as f:
            f.write(encrypted)
        
        # Set restrictive permissions
        os.chmod(self.credentials_path, 0o600)
    
    def load_tokens(self) -> Optional[Dict[str, any]]:
        """Load and decrypt tokens."""
        if not self.credentials_path.exists():
            return None
        
        with open(self.credentials_path, 'rb') as f:
            encrypted = f.read()
        
        # Decrypt
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
```

**Dependencies to Add:**
```
cryptography>=41.0.0
```

**Status:** ⏳ PENDING

---

### 3. **Insecure File Permissions**

**Severity:** 🔴 HIGH  
**File:** `src/auth.py` (line 179)  
**Issue:** Credentials file created with default permissions

**Current Implementation:**
```python
self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
# ❌ No permission restrictions
```

**Risk:**
- Other users on system can read credentials
- Insufficient protection for sensitive data

**Resolution:**
```python
# Set restrictive permissions on directory
self.credentials_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

# Set restrictive permissions on file
import os
os.chmod(self.credentials_path, 0o600)  # Owner read/write only
```

**Status:** ⏳ PENDING

---

### 4. **No Input Validation on OAuth Callback**

**Severity:** 🔴 HIGH  
**File:** `src/auth.py` (lines 245-268)  
**Issue:** OAuth callback doesn't validate state parameter

**Current Implementation:**
```python
def do_GET(self):
    query = urlparse(self.path).query
    params = parse_qs(query)
    
    if 'code' in params:
        code_container['code'] = params['code'][0]  # ❌ No validation
```

**Risk:**
- CSRF attacks on OAuth flow
- Authorization code interception
- No protection against replay attacks

**Resolution:**
```python
import secrets
import hashlib

class StravaAuthenticator:
    def __init__(self, ...):
        # ...
        self.state = None  # Will store CSRF token
    
    def get_authorization_url(self) -> str:
        """Generate authorization URL with CSRF protection."""
        client = Client()
        
        # Generate cryptographically secure state token
        self.state = secrets.token_urlsafe(32)
        
        url = client.authorization_url(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=['activity:read_all', 'profile:read_all'],
            state=self.state  # ✓ Add state parameter
        )
        return url
    
    def _wait_for_callback(self) -> str:
        """Wait for callback with state validation."""
        code_container = {'code': None, 'state': None}
        authenticator = self  # Capture self for inner class
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = urlparse(self.path).query
                params = parse_qs(query)
                
                # Validate state parameter
                if 'state' not in params:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<h1>Error: Missing state parameter</h1>")
                    return
                
                received_state = params['state'][0]
                if received_state != authenticator.state:
                    self.send_response(403)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<h1>Error: Invalid state parameter (CSRF detected)</h1>")
                    return
                
                # State validated, proceed
                if 'code' in params:
                    code_container['code'] = params['code'][0]
                    code_container['state'] = received_state
                    # ... success response
```

**Status:** ⏳ PENDING

---

## 🟡 MEDIUM PRIORITY FINDINGS

### 5. **Insufficient Logging of Security Events**

**Severity:** 🟡 MEDIUM  
**Issue:** No audit logging for authentication events

**Resolution:**
```python
import logging
from datetime import datetime

# Create security audit logger
security_logger = logging.getLogger('security_audit')
security_handler = logging.FileHandler('logs/security_audit.log')
security_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

# Log security events
def log_security_event(event_type: str, details: dict):
    """Log security-relevant events."""
    security_logger.info(f"{event_type}: {json.dumps(details)}")

# Usage in auth.py
def authenticate(self):
    log_security_event('AUTH_START', {'timestamp': datetime.utcnow().isoformat()})
    # ... authentication logic
    log_security_event('AUTH_SUCCESS', {'timestamp': datetime.utcnow().isoformat()})

def refresh_access_token(self, refresh_token: str):
    log_security_event('TOKEN_REFRESH', {'timestamp': datetime.utcnow().isoformat()})
    # ... refresh logic
```

**Status:** ⏳ PENDING

---

### 6. **No Rate Limiting on OAuth Callback Server**

**Severity:** 🟡 MEDIUM  
**File:** `src/auth.py` (lines 274-280)  
**Issue:** Local HTTP server has no rate limiting

**Risk:**
- Potential for DoS on local callback server
- No protection against brute force attempts

**Resolution:**
```python
from collections import defaultdict
from time import time

class RateLimitedCallbackHandler(BaseHTTPRequestHandler):
    # Class-level rate limit tracking
    request_counts = defaultdict(list)
    MAX_REQUESTS = 10
    TIME_WINDOW = 60  # seconds
    
    def do_GET(self):
        # Get client IP
        client_ip = self.client_address[0]
        
        # Check rate limit
        now = time()
        self.request_counts[client_ip] = [
            t for t in self.request_counts[client_ip]
            if now - t < self.TIME_WINDOW
        ]
        
        if len(self.request_counts[client_ip]) >= self.MAX_REQUESTS:
            self.send_response(429)  # Too Many Requests
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Rate limit exceeded</h1>")
            return
        
        self.request_counts[client_ip].append(now)
        
        # Continue with normal processing
        # ...
```

**Status:** ⏳ PENDING

---

### 7. **Missing Security Headers in OAuth Callback**

**Severity:** 🟡 MEDIUM  
**File:** `src/auth.py` (lines 254-265)  
**Issue:** HTTP response lacks security headers

**Resolution:**
```python
def do_GET(self):
    # ... validation logic
    
    # Send response with security headers
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.send_header('X-Content-Type-Options', 'nosniff')
    self.send_header('X-Frame-Options', 'DENY')
    self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'")
    self.send_header('Referrer-Policy', 'no-referrer')
    self.end_headers()
    # ...
```

**Status:** ⏳ PENDING

---

## 🟢 LOW PRIORITY / BEST PRACTICES

### 8. **Add Secrets Scanning to CI/CD**

**Recommendation:** Implement automated secrets detection

**Tools:**
- `git-secrets` - Prevents committing secrets
- `truffleHog` - Scans git history for secrets
- `detect-secrets` - Pre-commit hook for secret detection

**Implementation:**
```bash
# Install pre-commit hooks
pip install pre-commit detect-secrets

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
EOF

# Initialize
pre-commit install
detect-secrets scan > .secrets.baseline
```

**Status:** ⏳ PENDING

---

### 9. **Add Security Documentation**

**Recommendation:** Create SECURITY.md file

**Content:**
```markdown
# Security Policy

## Reporting Security Issues

Please report security vulnerabilities to: [your-email]

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Best Practices

1. Never commit .env files
2. Rotate API credentials regularly
3. Use encrypted token storage
4. Keep dependencies updated
5. Review security audit logs

## Known Security Considerations

- OAuth tokens are stored locally
- Application requires Strava API credentials
- Local HTTP server used for OAuth callback
```

**Status:** ⏳ PENDING

---

## Implementation Priority

### Phase 1: IMMEDIATE (Within 24 hours)
1. ✅ **Revoke and rotate Strava API credentials**
2. ✅ **Remove .env from git history**
3. ✅ **Create .env.example template**
4. ✅ **Update documentation with security warnings**

### Phase 2: HIGH PRIORITY (Within 1 week)
5. ⏳ **Implement encrypted token storage**
6. ⏳ **Add file permission restrictions**
7. ⏳ **Implement OAuth CSRF protection (state parameter)**
8. ⏳ **Add security audit logging**

### Phase 3: MEDIUM PRIORITY (Within 2 weeks)
9. ⏳ **Add rate limiting to OAuth callback**
10. ⏳ **Add security headers to HTTP responses**
11. ⏳ **Implement secrets scanning in CI/CD**

### Phase 4: ONGOING
12. ⏳ **Regular security audits**
13. ⏳ **Dependency vulnerability scanning**
14. ⏳ **Security documentation maintenance**

---

## Verification Checklist

After implementing fixes, verify:

- [ ] No credentials in git history
- [ ] .env file is gitignored and not tracked
- [ ] Tokens are encrypted at rest
- [ ] File permissions are restrictive (0o600 for credentials)
- [ ] OAuth flow includes state parameter validation
- [ ] Security events are logged
- [ ] Rate limiting is active
- [ ] Security headers are present
- [ ] Pre-commit hooks prevent secret commits
- [ ] SECURITY.md file exists
- [ ] Documentation updated with security best practices

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Strava API Security Best Practices](https://developers.strava.com/docs/authentication/)
- [OAuth 2.0 Security Best Current Practice](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [Python Cryptography Documentation](https://cryptography.io/)

---

## Contact

For security concerns, contact: [Maintainer Email]

**Last Updated:** 2026-03-14  
**Next Review:** 2026-04-14