import typer
import sys
import os
import logging
import requests
from oauthlib.oauth2 import WebApplicationClient
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

# Init Requests Cache
session = CachedSession(
    "discogs_api_cache",
    backend="sqlite",
    expire_after=1800
)
DISCOGS_DATA = {}
DISCOGS_KEY = os.getenv("DISCOGS_KEY")
DISCOGS_SECRET = os.getenv("DISCOGS_SECRET")
DISCOGS_API_TOKEN = None

# Initialize Rich's console
console = Console()
app = typer.Typer(
    name="DiMMS-CLI: Discogs Music Metadata Search",
    help="A lightweight metadata search tool for Discogs.",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_short=False
)

# OAuth
client = WebApplicationClient(str(DISCOGS_KEY))
auth_url = "https://www.discogs.com/oauth/authorize"

url = client.prepare_request_uri(
    auth_url,
    scope = "read:user",
)
data = client.prepare_request_body(
    client_id=DISCOGS_KEY,
    client_secret=DISCOGS_SECRET,
)

token_url = "https://api.discogs.com/oauth/request_token"
res = requests.post(token_url, data=data)
print(res)



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

# Discogs API
def get_discogs_api_token():
    logger.info("get_discogs_api_token(): Getting Discogs API Token")
    global DISCOGS_API_TOKEN
    


if __name__ == "__main__":
    app()
