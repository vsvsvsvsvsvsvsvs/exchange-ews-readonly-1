# exchange-ews-readonly

OpenClaw AgentSkill for strict read-only access to on-prem Exchange via EWS (`exchangelib`).

## Quickstart

```bash
cd /Users/vsevolodiakovlev/Documents/New\ project/exchange-ews-readonly
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Setup Env

Edit `.env` with your Exchange values:

```env
EXCHANGE_EWS_SERVER=mail.example.local
EXCHANGE_EWS_EMAIL=user@example.local
EXCHANGE_EWS_USERNAME=EXAMPLE\\user
EXCHANGE_EWS_PASSWORD=change-me
EXCHANGE_EWS_AUTH_TYPE=NTLM
EXCHANGE_EWS_VERIFY_TLS=true
EXCHANGE_EWS_TIMEOUT_SEC=30
```

Notes:
- `EXCHANGE_EWS_USERNAME` is optional; if empty, `EXCHANGE_EWS_EMAIL` is used.
- `EXCHANGE_EWS_AUTH_TYPE` supports `NTLM` (default) and `BASIC`.

## Commands

```bash
python scripts/ews_read.py --json health
python scripts/ews_read.py --json list --limit 10 --preview 500
python scripts/ews_read.py --json get --id "<ews-item-id>" --preview 500
python scripts/ews_read.py --json search --query "invoice" --days 7 --limit 10 --preview 500
```

## Read-Only Limits And Restrictions

Allowed actions:
- `health`
- `list`
- `get`
- `search`

Blocked operations include:
- `send`, `reply`, `forward`
- `delete`, `move`, `copy`
- `mark-read`, `mark-unread`, `update`
- `save`, `create`, `draft`, `create-draft`
- any unknown action

Any blocked action returns:

```text
READ_ONLY_VIOLATION: write operations are disabled
```

Hard limits:
- list default `10`, max `50`
- search days default `7`, max `30`
- preview default `500`, max `1000`

## Non-Goals

- No sending emails
- No reply/forward workflows
- No delete/move/copy operations
- No marking read/unread
- No update/save/create-draft or any mailbox mutation

## Troubleshooting

1. NTLM fails (401 Unauthorized)
- Verify `EXCHANGE_EWS_AUTH_TYPE=NTLM`.
- Verify username format `DOMAIN\user` (example: `EXAMPLE\user`).
- Confirm mailbox permissions for this account.

2. BASIC fails (401 Unauthorized)
- Verify Exchange EWS virtual directory allows BASIC auth.
- Set `EXCHANGE_EWS_AUTH_TYPE=BASIC`.

3. TLS/SSL certificate errors
- Keep `EXCHANGE_EWS_VERIFY_TLS=true` in production.
- For internal lab/testing only, set `EXCHANGE_EWS_VERIFY_TLS=false`.

4. Wrong server or timeout
- `EXCHANGE_EWS_SERVER` must be host only, no scheme/path.
- Increase `EXCHANGE_EWS_TIMEOUT_SEC` if network is slow.

5. Missing/invalid env values
- Re-check required variables:
  `EXCHANGE_EWS_SERVER`, `EXCHANGE_EWS_EMAIL`, `EXCHANGE_EWS_PASSWORD`.
- Ensure `EXCHANGE_EWS_TIMEOUT_SEC` is integer in `1..300`.
