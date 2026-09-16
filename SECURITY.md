# Security Policy

## Supported versions

Only the latest catalog release (root `VERSION`) receives security
fixes. Older snapshots are not patched.

## Reporting a vulnerability

Email **shanewasahmed@gmail.com** with:

- Affected plugin and version (`VERSION` plus plugin name).
- Steps to reproduce and impact.
- Any suggested fix (optional).

Do not open a public issue for an unpatched vulnerability. Expect an
acknowledgement within 7 days and a fix or mitigation plan once the
report is confirmed.

## Scope notes

- Plugin hook scripts and `tools/*.py` run with the user's own
  privileges inside their agent harness; review them before installing.
- This repository never asks for credentials and ships no networked
  services; treat any such request as suspicious.
