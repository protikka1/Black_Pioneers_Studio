# Security Policy

## Supported Versions

Security updates are currently provided for the latest version of **Black Pioneers Studio**.

| Version | Supported |
| --- | --- |
| Latest `main` branch | Yes |
| Older releases | No |

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Report vulnerabilities privately through GitHub private vulnerability reporting, if enabled, or through a private contact method listed in the repository owner's GitHub profile.

Include a description, reproduction steps, affected components, possible impact, logs, screenshots, and suggested remediation when available.

## Sensitive Information

Do not include passwords, API keys, access tokens, private certificates, personal information, databases, unauthorized media, or `.env` file contents in reports, commits, issues, or pull requests.

## Automated Security Checks

Pull requests and changes to `main` are checked with CodeQL, Bandit, and
`pip-audit`. Generated `build/` and `dist/` bundles are intentionally excluded
from version control and must be rebuilt from reviewed source code.
