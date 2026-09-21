#!/usr/bin/env python3
"""Preflight live-budget gate (mock-safe).

Checks TABPFN_TOKEN presence, defaults TABPFN_DEV_N to 60, and **blocks
full-table live** when a token is set without a safe sample_n / DEV_N.

Modes:
  --mock         expect empty TABPFN_TOKEN (default for judge/demo)
  --live-check   expect token set AND DEV_N / sample_n in 40–80

Usage (from repo root):
  TABPFN_TOKEN= python scripts/preflight_live_budget.py --mock
  python scripts/preflight_live_budget.py --live-check
  python scripts/preflight.sh --mock
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_DEV_N = 60
SAFE_MIN = 40
SAFE_MAX = 80
FIXTURE_CSV = (
    ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"
)


def _fixture_rows() -> int:
    if not FIXTURE_CSV.is_file():
        return 1200  # known freight fixture size
    # header + rows
    with FIXTURE_CSV.open("r", encoding="utf-8") as f:
        n = sum(1 for _ in f) - 1
    return max(n, 1)


def _token_set() -> bool:
    return bool(os.environ.get("TABPFN_TOKEN", "").strip())


def _resolve_dev_n(
    sample_n: str | None,
    *,
    set_default: bool = True,
) -> tuple[int | None, str]:
    """Return (resolved_n or None for full, source label).

    None means full-table / missing / empty / 0.
    When sample_n is omitted and TABPFN_DEV_N unset, default to 60
    (and optionally export TABPFN_DEV_N=60 into the process env).
    """
    if sample_n is not None:
        raw = str(sample_n).strip()
        if raw == "" or raw.lower() in {"full", "all", "none"}:
            return None, "sample_n=full/empty"
        try:
            n = int(raw)
        except ValueError:
            return None, f"sample_n=invalid({raw!r})"
        if n <= 0:
            return None, "sample_n<=0 (full)"
        return n, "sample_n"

    env_raw = os.environ.get("TABPFN_DEV_N", "").strip()
    if env_raw:
        try:
            n = int(env_raw)
        except ValueError:
            return None, f"TABPFN_DEV_N=invalid({env_raw!r})"
        if n <= 0:
            return None, "TABPFN_DEV_N<=0 (full)"
        return n, "TABPFN_DEV_N"

    if set_default:
        os.environ["TABPFN_DEV_N"] = str(DEFAULT_DEV_N)
        return DEFAULT_DEV_N, "default→TABPFN_DEV_N=60"
    return None, "unset"


def _chip_summary(*, sample_n: int | None, has_token: bool) -> dict:
    try:
        from apps.desk.dev_sample import live_budget_chip

        return live_budget_chip(sample_n=sample_n, has_token=has_token)
    except Exception as exc:  # pragma: no cover - import soft-fail
        planned = int(sample_n) if sample_n is not None else DEFAULT_DEV_N
        mode = "live" if has_token else "mock"
        return {
            "mode": mode,
            "label": (
                f"Live budget · n={planned} · est n/a"
                if has_token
                else f"Mock · no live spend · planned n={planned}"
            ),
            "sample_n": planned,
            "est_usd": None,
            "import_error": str(exc),
        }


def is_full_table_live(
    *,
    has_token: bool,
    resolved_n: int | None,
    fixture_rows: int | None = None,
) -> bool:
    """True when token is set and sample looks like full-table / missing."""
    if not has_token:
        return False
    rows = fixture_rows if fixture_rows is not None else _fixture_rows()
    if resolved_n is None:
        return True
    if resolved_n >= rows:
        return True
    return False


def run_preflight(
    *,
    mode: str = "mock",
    sample_n: str | None = None,
    set_default: bool = True,
    stream=None,
) -> int:
    """Run checks. Return 0 on ok, non-zero on fail."""
    out = stream or sys.stdout
    has_token = _token_set()
    resolved, source = _resolve_dev_n(sample_n, set_default=set_default)
    rows = _fixture_rows()
    chip = _chip_summary(sample_n=resolved, has_token=has_token)

    print("=== TabPFN live-budget preflight ===", file=out)
    print(
        f"TABPFN_TOKEN: {'SET' if has_token else 'unset/empty'}",
        file=out,
    )
    print(
        f"TABPFN_DEV_N / sample_n: resolved n={resolved} ({source})",
        file=out,
    )
    print(f"Fixture rows (freight): {rows}", file=out)
    print(
        f"Live-budget chip: {chip.get('label') or chip}",
        file=out,
    )
    if chip.get("est_usd") is not None:
        print(f"Rough est (mock formula): ~${chip['est_usd']:.2f}", file=out)

    rc = 0
    if mode == "mock":
        if has_token:
            print(
                "FAIL [--mock]: TABPFN_TOKEN is set. "
                "Re-run with TABPFN_TOKEN= for mock path.",
                file=out,
            )
            rc = 2
        else:
            print("OK [--mock]: empty token · mock path clear.", file=out)
    elif mode == "live-check":
        if not has_token:
            print(
                "FAIL [--live-check]: TABPFN_TOKEN unset. "
                "Set token for live path (or use --mock).",
                file=out,
            )
            rc = 3
        elif is_full_table_live(
            has_token=True, resolved_n=resolved, fixture_rows=rows
        ):
            print(
                "FAIL [--live-check]: full-table live BLOCKED. "
                "Use sample_n 40–80 or TABPFN_DEV_N=60 "
                f"(fixture has {rows} rows; resolved n={resolved}).",
                file=out,
            )
            rc = 4
        elif resolved is None or not (SAFE_MIN <= resolved <= SAFE_MAX):
            print(
                f"FAIL [--live-check]: DEV_N/sample_n={resolved} "
                f"not in safe band {SAFE_MIN}–{SAFE_MAX}. "
                "Use sample_n 40–80 / TABPFN_DEV_N=60.",
                file=out,
            )
            rc = 5
        else:
            print(
                f"OK [--live-check]: token set · n={resolved} in "
                f"{SAFE_MIN}–{SAFE_MAX} · live budget clear.",
                file=out,
            )
    else:
        print(f"FAIL: unknown mode {mode!r}", file=out)
        rc = 1

    # Always block full-table live regardless of mode when token set
    if has_token and is_full_table_live(
        has_token=True, resolved_n=resolved, fixture_rows=rows
    ):
        if rc == 0:
            print(
                "FAIL: full-table live BLOCKED. "
                "Use sample_n 40–80 / TABPFN_DEV_N=60.",
                file=out,
            )
            rc = 4
        else:
            print(
                "(also: full-table live would be blocked — "
                "use sample_n 40–80 / TABPFN_DEV_N=60)",
                file=out,
            )

    return rc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group()
    g.add_argument(
        "--mock",
        action="store_const",
        const="mock",
        dest="mode",
        help="Expect empty TABPFN_TOKEN (default)",
    )
    g.add_argument(
        "--live-check",
        action="store_const",
        const="live-check",
        dest="mode",
        help="Expect token + DEV_N/sample_n in 40–80",
    )
    p.add_argument(
        "--sample-n",
        default=None,
        help="Optional explicit sample_n (overrides TABPFN_DEV_N)",
    )
    p.add_argument(
        "--no-default",
        action="store_true",
        help="Do not force-default TABPFN_DEV_N=60 when unset",
    )
    p.set_defaults(mode="mock")
    args = p.parse_args(argv)
    return run_preflight(
        mode=args.mode,
        sample_n=args.sample_n,
        set_default=not args.no_default,
    )


if __name__ == "__main__":
    raise SystemExit(main())
