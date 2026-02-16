#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

from exchange_ews_readonly import (
    ConfigError,
    EwsReadonlyService,
    MessageNotFoundError,
    ReadOnlyViolationError,
    Settings,
)
from exchange_ews_readonly.client import EwsConnectionError
from exchange_ews_readonly.guards import assert_read_only
from exchange_ews_readonly.logging_utils import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ews_read",
        description="Read-only EWS CLI for on-prem Exchange (NTLM/BASIC)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output (default behavior)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health", help="Check EWS connectivity and inbox read access")

    p_list = subparsers.add_parser("list", help="List latest messages from Inbox")
    p_list.add_argument("--limit", type=int, default=None, help="Message count (default 10, max 50)")
    p_list.add_argument("--preview", type=int, default=None, help="Body preview length (default 500, max 1000)")

    p_get = subparsers.add_parser("get", help="Get message by EWS item id")
    p_get.add_argument("--id", required=True, help="EWS message id")
    p_get.add_argument("--preview", type=int, default=None, help="Body preview length (default 500, max 1000)")

    p_search = subparsers.add_parser("search", help="Search recent messages in Inbox")
    p_search.add_argument("--query", default="", help="Search substring")
    p_search.add_argument("--days", type=int, default=None, help="Lookback days (default 7, max 30)")
    p_search.add_argument("--limit", type=int, default=None, help="Result count (default 10, max 50)")
    p_search.add_argument("--preview", type=int, default=None, help="Body preview length (default 500, max 1000)")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        return _fail(str(exc), code=2)

    logger = configure_logging(secrets=[settings.password])
    service = EwsReadonlyService(settings=settings)

    try:
        command = args.command
        assert_read_only(command)

        if command == "health":
            result = service.health().to_dict()
        elif command == "list":
            result = [item.to_dict() for item in service.list_messages(limit=args.limit, preview=args.preview)]
        elif command == "get":
            result = service.get_message(message_id=args.id, preview=args.preview).to_dict()
        elif command == "search":
            result = [
                item.to_dict()
                for item in service.search_messages(
                    query=args.query,
                    days=args.days,
                    limit=args.limit,
                    preview=args.preview,
                )
            ]
        else:
            # Defensive fallback: unknown action is always denied.
            raise ReadOnlyViolationError()
    except ReadOnlyViolationError as exc:
        return _fail(str(exc), code=3)
    except ValueError as exc:
        return _fail(str(exc), code=2)
    except MessageNotFoundError as exc:
        return _fail(str(exc), code=4)
    except EwsConnectionError as exc:
        return _fail(str(exc), code=5)
    except Exception as exc:  # pragma: no cover - defensive runtime handling
        logger.error("Unexpected runtime error: %s", exc)
        return _fail("EWS_RUNTIME_ERROR", code=1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _fail(message: str, code: int) -> int:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
