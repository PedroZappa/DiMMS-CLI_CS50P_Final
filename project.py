import typer
import sys
import os
import logging
from typing import Dict, Any
from oauthlib.oauth2 import WebApplicationClient
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3.util.retry import Retry
from rich.console import Console
from rich.table import Table
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
BASE_URL = "https://api.discogs.com"
CACHED_SESSION = CachedSession("discogs_api_cache", backend="sqlite", expire_after=1800)
DISCOGS_DATA = {}
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

# Initialize Rich's console
console = Console()
app = typer.Typer(
    name="DiMMS-CLI: Discogs Music Metadata Search",
    help="A lightweight metadata search tool for Discogs.",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_short=False,
)


# Entry Point
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
):
    """
    Main entry point for DiMMS-CLI.

    :param ctx: The Typer context object
    :type ctx: typer.Context
    """
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
            "[yellow]⚠  No DISCOGS_TOKEN found.\nPlease set your Personal Access Token.[/yellow]"
        )
    if ctx.invoked_subcommand is None:
        ctx.exit(0)


# Authentication
def get_discogs_headers():
    """
    Get headers for Discogs API requests.

    :raise TypeError:
    :return: A dictionary of headers
    :rtype: dict
    """
    if not DISCOGS_TOKEN:
        raise ValueError("DISCOGS_TOKEN environment variable not set")

    return {
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": "DiMMS-CLI/1.0",
    }


def test_authentication():
    """
    Test if authentication is working.

    :except Exception: Authentication error
    :return: True if authentication is successful, False otherwise
    :rtype: bool
    """
    try:
        headers = get_discogs_headers()
        response = CACHED_SESSION.get(f"{BASE_URL}/oauth/identity", headers=headers)

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


@app.command()
def hello(name: str = "world"):
    print(f"Hello from {name}")


# Commands
@app.command()
def search_artists(artist_name: str):
    """
    Search for an artist by name.

    :param artist_name: The name of the artist to search for
    :type artist_name: str
    :except Exception: Search error
    """
    DISCOGS_DATA = get_artists_data(artist_name)

    table = Table(title=f"Search Results for: {artist_name}")
    table.add_column("Name", justify="right", style="cyan", no_wrap=True)
    table.add_column("ID", justify="left", style="magenta", no_wrap=True)
    for artist in DISCOGS_DATA["artists"]:
        table.add_row(
            artist["title"],
            str(artist["id"]),
        )
    
    console.print(table)


def get_artists_data(artist_name: str) -> Dict[str, Any]:
    """
    Search for artists by name using the Discogs API.

    Performs a search query against the Discogs database to find artists matching
    the provided name. Returns up to 6 results with artist information including
    title, ID, and URI.

    :param artist_name: The name of the artist to search for. Can be a partial
    or full artist name.
    :type artist_name: str
    :returns: A dictionary containing the found artists data
    :rtype: Dict[str, Any]
    """
    result_dict = {}
    try:
        headers = get_discogs_headers()
        params = {"q": artist_name, "type": "artist"}

        response = CACHED_SESSION.get(
            f"{BASE_URL}/database/search", headers=headers, params=params
        )

        if response.status_code == 200:
            data = response.json()
            result_dict["total_results"] = data.get("pagination", {}).get("items", 0)
            result_dict["artists"] = []

            for result in data.get("results", [])[:6]:  # Show first 6
                artist_info = {
                    "title": result.get("title"),
                    "id": result.get("id"),
                    "uri": result.get("uri"),
                }
                result_dict["artists"].append(artist_info)
        else:
            result_dict["error"] = f"Error: {response.status_code}"

    except Exception as e:
        logger.error(f"Search error: {e}")
        result_dict["error"] = str(e)

    return result_dict


if __name__ == "__main__":
    app()
