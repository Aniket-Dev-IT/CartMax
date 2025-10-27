# Security Policy

## Overview

CartMax is committed to providing a secure, reliable e-commerce platform. This document outlines our security practices, supported versions, and how to responsibly report security vulnerabilities.

## Supported Versions

| Version | Released | End of Support | Status |
|---------|----------|-----------------|--------|
| 1.0.x   | 2025-10-27 | 2026-10-27 | ✅ Supported |
| 0.9.x   | N/A | N/A | ❌ Not Supported |

We recommend always using the latest version of CartMax for the best security and features.

## Reporting a Vulnerability

### Responsible Disclosure

If you discover a security vulnerability in CartMax, please report it responsibly to us. We appreciate security researchers and community members reporting vulnerabilities.

**Do NOT:**
- Post security vulnerabilities publicly on GitHub Issues
- Disclose the vulnerability on social media or forums
- Attempt to exploit the vulnerability further
- Share vulnerability details with others

**Do:**
- Report to us privately via email
- Provide detailed information about the vulnerability
- Include proof of concept if possible
- Give us reasonable time to fix before public disclosure

### How to Report

1. **Email**: Send your report to `aniket.kumar.devpro@gmail.com`
2. **Subject**: Start with `[SECURITY]` tag
3. **Include**:
   - Description of the vulnerability
   - Type of vulnerability (SQL injection, XSS, etc.)
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

Example report format:
```
Subject: [SECURITY] Cross-Site Scripting (XSS) vulnerability in product comments

Description:
The product detail page's comment section is vulnerable to Stored XSS attacks.
User comments are not properly sanitized before rendering in templates.

Steps to Reproduce:
1. Add a new product review with HTML/JavaScript payload:
   <img src=x onerror="alert('XSS')">
2. Click Submit
3. Visit the product detail page
4. The JavaScript will execute

Potential Impact:
- Session hijacking through cookie theft
- Malware distribution
- Defacement of product pages
- User data theft

Suggested Fix:
Use Django's template auto-escaping or implement input sanitization
```

### Our Response

We will:
1. Acknowledge receipt of your report within 48 hours
2. Investigate the vulnerability
3. Develop and test a fix
4. Release a patch (typically within 7-14 days for critical issues)
5. Credit you if desired
6. Notify you of the public disclosure

### Reporting Timeline

- **Critical Vulnerabilities**: Fixed within 7 days
- **High Severity**: Fixed within 14 days
- **Medium Severity**: Fixed within 30 days
- **Low Severity**: Fixed in next regular release

## Security Best Practices

### For Users/Administrators

#### Installation & Setup
- ✅ Always download CartMax from official GitHub repository
- ✅ Verify checksums before installation
- ✅ Keep Python and Django updated
- ✅ Use HTTPS in production
- ✅ Set `DEBUG = False` in production
- ✅ Use a strong, unique `SECRET_KEY`

#### Database Security
- ✅ Use PostgreSQL or MySQL in production (not SQLite)
- ✅ Enable database encryption at rest
- ✅ Regular automated backups
- ✅ Restrict database access to application servers only
- ✅ Use strong database credentials

#### Server Security
- ✅ Keep your server OS updated
- ✅ Use firewall rules (allow only necessary ports)
- ✅ Implement SSL/TLS certificates (Let's Encrypt)
- ✅ Regular security patches
- ✅ Monitor server logs for suspicious activity
- ✅ Use Web Application Firewall (WAF)

#### Application Security
- ✅ Keep CartMax updated to latest version
- ✅ Keep all dependencies updated
- ✅ Regular security audits
- ✅ Enable CSRF protection (enabled by default)
- ✅ Use secure session settings
- ✅ Enable security headers

#### User Management
- ✅ Create strong admin passwords
- ✅ Limit admin user accounts
- ✅ Regular password changes
- ✅ Two-factor authentication (planned feature)
- ✅ Audit user permissions regularly

### For Developers

#### Code Security
- ✅ Never hardcode sensitive information (API keys, passwords, etc.)
- ✅ Use environment variables for configuration
- ✅ Validate and sanitize all user inputs
- ✅ Use parameterized queries to prevent SQL injection
- ✅ Escape output to prevent XSS attacks
- ✅ Use CSRF tokens for form submissions

#### Dependencies
- ✅ Keep dependencies updated
- ✅ Use `pip-audit` to check for vulnerabilities
- ✅ Review new package versions before updating
- ✅ Remove unused dependencies
- ✅ Minimize third-party dependencies

#### Testing
- ✅ Write security-focused tests
- ✅ Test authentication and authorization
- ✅ Test input validation
- ✅ Test for SQL injection vulnerabilities
- ✅ Test for XSS vulnerabilities
- ✅ Use security linters

### Built-in Security Features

CartMax includes several security features by default:

#### Django Security Features
- **CSRF Protection**: Enabled by default for all POST requests
- **SQL Injection Prevention**: Django ORM parameterization
- **XSS Protection**: Template auto-escaping
- **Clickjacking Protection**: X-Frame-Options header
- **MIME Type Sniffing Protection**: X-Content-Type-Options header
- **Security Redirect**: SECURE_HSTS_SECONDS, SECURE_SSL_REDIRECT

#### Application-Level Security
- **Password Hashing**: PBKDF2 with SHA256 (Django's default)
- **Session Security**: Secure session cookies
- **Admin Authentication**: Login required for admin panel
- **User Input Validation**: Form validation on frontend and backend
- **Rate Limiting**: Ready for implementation

## Security Checklist for Production

Before deploying CartMax to production, ensure:

### Environment
- [ ] Set `DEBUG = False`
- [ ] Use strong `SECRET_KEY` (40+ characters)
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Set `SECURE_SSL_REDIRECT = True`
- [ ] Set `SESSION_COOKIE_SECURE = True`
- [ ] Set `CSRF_COOKIE_SECURE = True`
- [ ] Set `SECURE_HSTS_SECONDS = 31536000` (1 year)
- [ ] Set `X_FRAME_OPTIONS = 'DENY'`

### Database
- [ ] Use PostgreSQL or MySQL (not SQLite)
- [ ] Strong database password
- [ ] Database backups configured
- [ ] Database encryption enabled
- [ ] Limited database access

### Server
- [ ] OS security patches applied
- [ ] Firewall configured
- [ ] SSL/TLS certificate installed
- [ ] HTTPS only (HTTP redirects to HTTPS)
- [ ] Web Application Firewall configured
- [ ] DDoS protection enabled
- [ ] Server monitoring active

### Application
- [ ] All dependencies updated
- [ ] CartMax updated to latest version
- [ ] Static files collected
- [ ] Logs configured and monitored
- [ ] Error reporting configured
- [ ] Admin user password strong
- [ ] Unnecessary debug files removed
- [ ] `.env` file not in repository
- [ ] `db.sqlite3` not in production

### Monitoring
- [ ] Error tracking (Sentry) configured
- [ ] Performance monitoring active
- [ ] Security scanning scheduled
- [ ] Regular backups tested
- [ ] Log aggregation configured
- [ ] Intrusion detection enabled

## Security Headers

CartMax can be configured to send the following security headers:

```python
# Recommended security headers configuration
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True

X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "trusted-cdn.com"),
}
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY_REPORT_ONLY = False
```

## Password Policy

### User Password Requirements
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, and symbols
- No common/dictionary words
- Not similar to username or email

### Admin Account Security
- Strong password (15+ characters recommended)
- Regular password changes (every 90 days)
- Consider password manager
- Enable two-factor authentication (planned)

## Data Protection

### User Data
- Payment information: Never stored locally (use payment gateway)
- Personal information: Encrypted in transit (HTTPS)
- Email addresses: Used for order notifications only
- Browsing history: Not shared with third parties

### Data Retention
- Order data: Retained for legal/financial purposes
- Logs: 30-90 days retention (security policy)
- Deleted accounts: Anonymized within 30 days
- Cookies: Session only (no persistent tracking)

## Compliance

CartMax is designed to help meet various security and compliance standards:

- **OWASP**: Follows OWASP Top 10 protections
- **PCI DSS**: Ready for PCI DSS compliance (with payment gateway)
- **GDPR**: Supports GDPR requirements
- **CCPA**: Supports CCPA requirements
- **SOC 2**: Architecture supports SOC 2 compliance

## Known Limitations

- SQLite database in development is not suitable for production multi-user environments
- Payment processing requires third-party integration (not built-in)
- Email notifications require SMTP server configuration
- Requires proper server security configuration for production use

## Security Updates

Subscribe to security updates:
- 👁️ Watch repository on GitHub
- ⭐ Star to get notifications
- 📧 Email: aniket.kumar.devpro@gmail.com
- 🔔 Enable GitHub notifications

## Contact

### Security Contact
- **Email**: aniket.kumar.devpro@gmail.com
- **Response Time**: Within 48 hours
- **Disclosure**: Coordinated disclosure policy

### Support
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: Check [README.md](README.md) and [docs/](docs/)

## External Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [Python Security Documentation](https://docs.python.org/3/library/security_warnings.html)
- [PCI DSS Compliance](https://www.pcisecuritystandards.org/)

## Frequently Asked Questions

### Q: Is CartMax secure for production use?
A: CartMax has been designed with security best practices in mind and includes many built-in security features. However, security also depends on proper configuration, server setup, and regular maintenance. Follow all recommendations in this security policy.

### Q: Where should I store sensitive data?
A: Never hardcode sensitive data. Use environment variables or secure configuration management tools. Keep `.env` files out of version control.

### Q: How do I update CartMax securely?
A: Always review changes before updating. Back up your database first. Update in a staging environment before production.

### Q: Do you conduct security audits?
A: Regular internal reviews are conducted. For professional security audits, please contact us.

### Q: How are dependencies managed?
A: Dependencies are carefully selected and regularly updated. We use `pip-audit` to check for known vulnerabilities.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-27 | Initial security policy |

**Last Updated:** October 27, 2025

**For security concerns, please email:** aniket.kumar.devpro@gmail.com
