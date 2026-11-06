# Security Policy

## Supported Versions
Only the latest release receives security patches.

## Reporting Vulnerabilities
Please **do not** open a public GitHub issue for security vulnerabilities.
Email the maintainer directly. Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

Expect a response within 72 hours and a patch within 7 days.

## Notes
- Never commit `.env` files or secrets to the repository
- Rotate `SECRET_KEY` before deploying to production
- The default SQLite setup is for local development only
