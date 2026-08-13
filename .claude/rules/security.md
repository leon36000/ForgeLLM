# Security rules

- Never expose or commit credentials, tokens, private model files or machine secrets.
- Do not register or modify runners, secrets, repository permissions or protection rules without explicit owner authorization.
- Do not execute untrusted fork code on self-hosted hardware.
- Pin third-party CI actions to full commit SHAs.
- Treat driver, firmware and destructive system changes as lab-operator actions.
