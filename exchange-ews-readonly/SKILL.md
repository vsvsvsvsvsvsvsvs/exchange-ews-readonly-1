---
name: exchange-ews-readonly
description: OpenClaw AgentSkill for read-only Exchange on-prem access via EWS (exchangelib). Use when users need mailbox health checks and message retrieval/search (`health`, `list`, `get`, `search`) with NTLM auth by default and optional BASIC auth. Enforce hard blocking for all write-like actions (send/reply/forward/delete/move/copy/mark read or unread/update/save/create draft and similar mutations).
---

# exchange-ews-readonly

Implement strict read-only Exchange EWS operations for OpenClaw.

## When To Use

Use this skill when the user needs to read Exchange mailbox data from on-prem EWS without any mailbox modifications:

- connectivity check (`health`)
- inbox listing (`list`)
- message fetch by id (`get`)
- inbox search (`search`)

## Environment

- `EXCHANGE_EWS_SERVER`
- `EXCHANGE_EWS_EMAIL`
- `EXCHANGE_EWS_USERNAME` (optional, fallback to email)
- `EXCHANGE_EWS_CRYPTO_KEY`
- `EXCHANGE_EWS_PASSWORD_ENC`
- `EXCHANGE_EWS_ALLOW_PLAINTEXT_PASSWORD` (optional migration fallback)
- `EXCHANGE_EWS_AUTH_TYPE` (`NTLM` default, optional `BASIC`)
- `EXCHANGE_EWS_VERIFY_TLS` (default `true`)
- `EXCHANGE_EWS_TIMEOUT_SEC` (default `30`)

## Limits

- `list`: default `10`, max `50`
- `search --days`: default `7`, max `30`
- `preview`: default `500`, max `1000`

Clamp values above max. Reject non-positive values.

## Commands And Examples

- `health`:
  `python scripts/ews_read.py --json health`
- `list`:
  `python scripts/ews_read.py --json list --limit 10 --preview 500`
- `get`:
  `python scripts/ews_read.py --json get --id "<ews-item-id>" --preview 500`
- `search`:
  `python scripts/ews_read.py --json search --query "invoice" --days 7 --limit 10 --preview 500`

## Security And Read-Only Notes

- Allow only: `health`, `list`, `get`, `search`.
- Reject any write operation with exact text:
  `READ_ONLY_VIOLATION: write operations are disabled`.
- Block all write-like actions: `send`, `reply`, `forward`, `delete`, `move`, `copy`, `mark-read`, `mark-unread`, `update`, `save`, `create`, `draft`, `create-draft`, and similar mutations.
- Never log credentials or raw secrets.
- Keep mailbox state immutable in all code paths.

- Never log credentials.
- Redact secrets in logs.
