"""Typer CLI: demo | mcp | gen | desk."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="tabpfn-hack",
    help="Domain-agnostic TabPFN-3.5 hackathon core (demo / mcp / gen / desk).",
    add_completion=False,
)
console = Console()


def _project_root() -> Path:
    from tabpfn_hack_core.domain import find_project_root

    return find_project_root()


def _maybe_dotenv(path) -> None:
    """Load .env unless DESK_NO_DOTENV=1 (tests: a local token must never leak in)."""
    import os

    if os.environ.get("DESK_NO_DOTENV", "").strip().lower() in {"1", "true", "yes"}:
        return
    from dotenv import load_dotenv

    load_dotenv(path)


@app.command()
def demo(
    mode: str = typer.Option(
        "mock",
        "--mode",
        "-m",
        help="Backend: mock|plus|thinking|fast|local (default mock; auto-falls back without token)",
    ),
    data: Optional[Path] = typer.Option(
        None, "--data", "-d", help="CSV path (default data/synthetic_table.csv)"
    ),
    domain_path: Optional[Path] = typer.Option(
        None, "--domain", help="Path to domain.yaml"
    ),
    out_dir: Path = typer.Option(
        Path("artifacts"), "--out", help="Artifact output directory"
    ),
) -> None:
    """Run end-to-end demo; works without TABPFN_TOKEN via mock backend."""

    from tabpfn_hack_core.demo.run_demo import run_demo

    root = _project_root()
    _maybe_dotenv(root / ".env")
    result = run_demo(
        root=root,
        mode=mode,
        data_path=data,
        domain_path=domain_path,
        out_dir=out_dir if out_dir.is_absolute() else root / out_dir,
    )
    console.print(f"[green]Demo OK[/green] mode={result['mode']} backend={result['backend']}")
    console.print(f"  metrics: {result['metrics']}")
    console.print(f"  report: {result['report_path']}")
    console.print(f"  predictions: {result['predictions_path']}")
    if result.get("warning"):
        console.print(f"[yellow]warning:[/yellow] {result['warning']}")


@app.command()
def mcp() -> None:
    """Start MCP stdio server exposing the 7 tools."""

    _maybe_dotenv(_project_root() / ".env")
    from tabpfn_hack_core.server.mcp_server import main as mcp_main

    mcp_main()


@app.command()
def gen(
    n: int = typer.Option(1000, "--n", help="Number of rows"),
    out: Path = typer.Option(
        Path("data/synthetic_table.csv"), "--out", help="Output CSV path"
    ),
    seed: int = typer.Option(42, "--seed"),
) -> None:
    """Generate synthetic messy-table CSV."""
    from tabpfn_hack_core.demo.run_demo import generate_synthetic_table

    root = _project_root()
    out_path = out if out.is_absolute() else root / out
    path = generate_synthetic_table(n=n, out=out_path, seed=seed)
    console.print(f"[green]Wrote[/green] {path} ({n} rows)")


@app.command()
def desk(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8765, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Dev auto-reload"),
) -> None:
    """Start the freight demurrage web desk (FastAPI)."""

    root = _project_root()
    _maybe_dotenv(root / ".env")
    try:
        import uvicorn
    except ImportError:
        console.print(
            "[red]Desk requires optional deps:[/red] pip install -e '.[desk]' "
            "(fastapi, uvicorn, jinja2, python-multipart)"
        )
        raise typer.Exit(code=1)

    import sys

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    console.print(f"[green]Desk[/green] http://{host}:{port}  (root={root})")
    uvicorn.run(
        "apps.desk.app:app",
        host=host,
        port=port,
        reload=reload,
        app_dir=str(root),
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
