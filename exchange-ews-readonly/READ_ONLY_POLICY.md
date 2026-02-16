# READ_ONLY_POLICY

This skill is strictly read-only.

## Allowed Actions

- `health`
- `list`
- `get`
- `search`

## Denied Actions

- Any action not in the allowed list.
- Explicitly denied examples:
  `send`, `reply`, `forward`, `delete`, `move`, `copy`,
  `mark-read`, `mark-unread`, `update`, `save`, `create`, `draft`, `create-draft`.

## Enforcement

- Guard layer uses explicit whitelist validation.
- Unknown actions are denied by default.
- Denied action always raises:

`READ_ONLY_VIOLATION: write operations are disabled`

## Logging Safety

- Never log raw credentials.
- Sanitize known sensitive patterns: password, token, auth/authorization.
