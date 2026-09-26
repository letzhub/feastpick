# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
| < 1.0   | No        |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Email the maintainer(s) listed on the GitHub repository profile, or use
**GitHub Security Advisories** (Security → Report a vulnerability) if enabled.

Include:

- FeastPick version (`GET /api/health`)
- Description and impact
- Steps to reproduce
- Any suggested fix

We aim to acknowledge reports within a few days.

## Deployment notes

FeastPick is designed for **trusted groups** (family, friends). Identity is a
first name stored in the browser. For internet-facing installs you should add:

- TLS termination
- Rate limiting / bot protection
- Optional access control (VPN, reverse-proxy auth, or an event PIN — not built-in yet)
- Regular backups of the SQLite volume

Do not treat board links as secret authentication by themselves if the threat
model includes hostile actors.
