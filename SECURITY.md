# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Instead, report them privately via GitHub's **[Security Advisories](../../security/advisories/new)**
("Report a vulnerability"), or by email to **security@mythoscope.io** (once available; until then,
use the private advisory).

Include: a description, steps to reproduce, affected component/version, and any suggested fix.
We aim to acknowledge reports within a few days.

## Scope

Mythoscope is a research tool intended to be run locally or self-hosted. The most relevant areas:
LLM/API key handling (`.env`), the fetch/cache layer, and the web server. Please flag anything
that could leak credentials, corrupt data, or allow unintended remote access.
