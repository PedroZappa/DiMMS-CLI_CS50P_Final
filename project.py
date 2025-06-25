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
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Init Requests Cache
session = CachedSession("discogs_api_cache", backend="sqlite", expire_after=1800)
DISCOGS_DATA = {}
DISCOGS_KEY = os.getenv("DISCOGS_KEY")
DISCOGS_SECRET = os.getenv("DISCOGS_SECRET")
DISCOGS_TOKEN = None
BASE_URL = "https://api.discogs.com"

# Initialize Rich's console
console = Console()
app = typer.Typer(
    name="DiMMS-CLI: Discogs Music Metadata Search",
    help="A lightweight metadata search tool for Discogs.",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_short=False,
)

# OAuth
# client = WebApplicationClient(str(DISCOGS_KEY))
# auth_url = "https://www.discogs.com/oauth/authorize"
#
# url = client.prepare_request_uri(
#     auth_url,
#     scope = "read:user",
# )
# data = client.prepare_request_body(
#     client_id=DISCOGS_KEY,
#     client_secret=DISCOGS_SECRET,
# )
#
# token_url = "https://api.discogs.com/oauth/request_token"
# res = requests.post(token_url, data=data)
# print(res)


def get_discogs_headers():
    """Get headers for Discogs API requests."""
    if not DISCOGS_TOKEN:
        raise ValueError("DISCOGS_TOKEN environment variable not set")

    return {
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": "DiMMS-CLI/1.0",
    }


def test_authentication():
    """Test if authentication is working."""
    try:
        headers = get_discogs_headers()
        response = session.get(f"{BASE_URL}/oauth/identity", headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            logger.info(f"Authenticated as: {user_data.get('username')}")
            return True
        else:
            logger.error(f"Authentication failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False


# Entry Point
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
):
    """Main entry point for DiMMS-CLI."""
    print("[bold green]Discogs Music Metadata Search[/bold green]")
    # Test authentication on startup
    if DISCOGS_TOKEN:
        if test_authentication():
            print("[green]✓ Authentication successful[/green]")
        else:
            print("[red]✗ Authentication failed[/red]")
            print("Please check your DISCOGS_TOKEN environment variable")
    else:
        print(
            "[yellow]⚠  No DISCOGS_TOKEN found. Please set your Personal Access Token.[/yellow]"
        )
    if ctx.invoked_subcommand is None:
        ctx.exit(0)


@app.command()
def hello(name: str = "world"):
    print(f"Hello from {name}")


@app.command()
def search_artist(artist_name: str):
    """Search for an artist."""
    try:
        headers = get_discogs_headers()
        params = {"q": artist_name, "type": "artist"}

        response = session.get(
            f"{BASE_URL}/database/search", headers=headers, params=params
        )

        if response.status_code == 200:
            data = response.json()
            print(f"Found {data.get('pagination', {}).get('items', 0)} results")

            for result in data.get("results", [])[:5]:  # Show first 5
                print(f"[bold]{result.get('title')}[/bold]")
                print(f"ID: {result.get('id')}")
                print(f"URI: {result.get('uri')}")
                print()
        else:
            print(f"[red]Error: {response.status_code}[/red]")

    except Exception as e:
        logger.error(f"Search error: {e}")


@app.command()
def get_albums():
    """Get user's collection (requires authentication)."""
    try:
        headers = get_discogs_headers()
        response = session.get(
            f"{BASE_URL}/users/{{username}}/collection/folders/0/releases",
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            print("Your collection:")
            for release in data.get("releases", [])[:10]:  # Show first 10
                basic_info = release.get("basic_information", {})
                print(f"[bold]{basic_info.get('title')}[/bold]")
                artists = [
                    artist.get("name") for artist in basic_info.get("artists", [])
                ]
                print(f"Artists: {', '.join(artists)}")
                print()
        else:
            print(f"[red]Error: {response.status_code}[/red]")

    except Exception as e:
        logger.error(f"Collection error: {e}")


# Discogs API
def get_discogs_api_token():
    logger.info("get_discogs_api_token(): Getting Discogs API Token")
    global DISCOGS_API_TOKEN


if __name__ == "__main__":
    app()
