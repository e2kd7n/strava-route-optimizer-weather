# Security Policy

## 🚨 Critical Security Notice

This project handles sensitive Strava API credentials and OAuth tokens. Please follow security best practices to protect your data.

## Reporting Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via:
- Email: [Maintainer - add your email]
- GitHub Security Advisories: Use the "Security" tab in the repository

We will respond to security reports within 48 hours.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Best Practices

### For Users

1. **Never commit `.env` files to git**
   - The `.env` file contains your API credentials
   - Always use `.env.example` as a template
   - Verify `.env` is in `.gitignore`

2. **Protect your API credentials**
   - Keep `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` private
   - Don't share credentials in screenshots or logs
   - Rotate credentials if exposed

3. **Secure token storage**
   - OAuth tokens are stored in `config/credentials.json`
   - This file should have restrictive permissions (0o600)
   - Consider encrypting tokens at rest (see SECURITY_RESOLUTION_PLAN.md)

4. **Keep dependencies updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

5. **Review security audit logs**
   - Check `logs/security_audit.log` regularly
   - Monitor for suspicious authentication attempts

### For Developers

1. **Use pre-commit hooks**
   ```bash
   pip install pre-commit detect-secrets
   pre-commit install
   ```

2. **Scan for secrets before committing**
   ```bash
   detect-secrets scan
   ```

3. **Review code for security issues**
   - Use static analysis tools (bandit, safety)
   - Follow OWASP guidelines
   - Implement input validation

4. **Test security features**
   - Verify OAuth CSRF protection
   - Test rate limiting
   - Validate file permissions

## Known Security Considerations

### Current Implementation

- **OAuth tokens stored locally**: Tokens are saved to `config/credentials.json`
- **Local HTTP server**: Used for OAuth callback on port 8000
- **File-based storage**: No database encryption by default
- **Single-user design**: Not designed for multi-tenant use

### Planned Improvements

See `SECURITY_RESOLUTION_PLAN.md` for detailed security enhancements:
- Encrypted token storage
- OAuth CSRF protection (state parameter)
- Security audit logging
- Rate limiting on OAuth callback
- Multi-user support with proper isolation

## Security Features

### Implemented

✅ **Environment variable protection**
- Credentials loaded from `.env` file
- `.env` is gitignored by default

✅ **OAuth 2.0 authentication**
- Standard OAuth flow with Strava
- Token refresh mechanism

✅ **Input validation**
- Client ID format validation
- Client secret length validation

### In Progress

⏳ **Encrypted token storage** (See Issue #9)
⏳ **CSRF protection** (See SECURITY_RESOLUTION_PLAN.md)
⏳ **Security audit logging** (See SECURITY_RESOLUTION_PLAN.md)
⏳ **Rate limiting** (See SECURITY_RESOLUTION_PLAN.md)

## Compliance

### Data Handling

- **Strava API Terms**: This application complies with Strava API Terms of Service
- **Data Storage**: Activity data is cached locally for performance
- **Data Retention**: Users control their own data storage
- **Data Deletion**: Delete `data/` and `cache/` directories to remove all data

### Privacy

- **No telemetry**: This application does not send usage data
- **Local processing**: All analysis happens on your machine
- **No third-party services**: Except Strava API and optional weather API

## Security Checklist for Deployment

Before deploying or sharing this application:

- [ ] Remove any `.env` files from git history
- [ ] Verify `.env` is in `.gitignore`
- [ ] Create `.env` from `.env.example` with your credentials
- [ ] Set restrictive file permissions on `config/credentials.json` (0o600)
- [ ] Review and rotate API credentials if previously exposed
- [ ] Enable security audit logging
- [ ] Install pre-commit hooks for secret detection
- [ ] Update all dependencies to latest secure versions
- [ ] Review `SECURITY_RESOLUTION_PLAN.md` for additional hardening

## Incident Response

If you discover a security vulnerability:

1. **Immediately revoke compromised credentials**
   - Go to https://www.strava.com/settings/api
   - Delete the compromised application
   - Create new credentials

2. **Remove credentials from git history**
   ```bash
   # Use BFG Repo-Cleaner or git filter-branch
   # See SECURITY_RESOLUTION_PLAN.md for details
   ```

3. **Notify affected parties**
   - If repository is public, notify users
   - Document the incident

4. **Implement fixes**
   - Follow remediation steps in SECURITY_RESOLUTION_PLAN.md
   - Update security documentation

5. **Post-incident review**
   - Analyze root cause
   - Update security practices
   - Improve detection mechanisms

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Strava API Documentation](https://developers.strava.com/docs/)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## Contact

For security concerns:
- Create a private security advisory on GitHub
- Email: [Add maintainer email]

---

**Last Updated:** 2026-03-14  
**Next Security Review:** 2026-04-14