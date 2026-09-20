"""Typer CLI: demo | mcp | gen."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="tabpfn-hack",
    help="Domain-agnostic TabPFN-3.5 hackathon core (demo / mcp / gen).",
    add_completion=False,
)
console = Console()


def _project_root() -> Path:
    from tabpfn_hack_core.domain import find_project_root

    return find_project_root()


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
    from dotenv import load_dotenv

    from tabpfn_hack_core.demo.run_demo import run_demo

    root = _project_root()
    load_dotenv(root / ".env")
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
    from dotenv import load_dotenv

    load_dotenv(_project_root() / ".env")
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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
