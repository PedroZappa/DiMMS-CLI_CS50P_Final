import typer
import sys
import os
import logging
import requests
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3.util.retry import Retry
from rich.console import Console
from rich.progress import track
from rich import print

# Init Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
discogs_data = {}

# Init Requests Cache
session = CachedSession(
    "discogs_api_cache",
    backend="sqlite",
    expire_after=1800
)

# Initialize Rich's console
console = Console()
app = typer.Typer(
    name="DiMMS-CLI: Discogs Music Metadata Search",
    help="A lightweight metadata search tool for Discogs.",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_short=False
)

# Entry Point
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, ):
    """Main entry point for DiMMS-CLI."""
    print("[bold green]Discogs Music Metadata Search[/bold green]")
    if ctx.invoked_subcommand is None:
        ctx.exit(0)


@app.command()
def hello(name: str = "world"):
    print(f"Hello from {name}")

@app.command()
def get_albums():
    print("Getting Albums")

if __name__ == "__main__":
    app()
