import typer
import sys
import os
import logging
import shlex
from typing import Dict, Any
from oauthlib.oauth2 import WebApplicationClient
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3.util.retry import Retry
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
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
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Run in interactive mode")
):
    """
    Main entry point for DiMMS-CLI.

    :param ctx: The Typer context object
    :type ctx: typer.Context
    :param interactive: Whether to run in interactive mode
    :type interactive: bool
    """
    global interactive_mode
    interactive_mode = interactive
    
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
    
    # If no subcommand is invoked and interactive mode is requested, start the loop
    if ctx.invoked_subcommand is None:
        if interactive:
            interactive_loop(ctx)
        else:
            # Show help if not in interactive mode and no command given
            print("\n[yellow]Use --interactive or -i for interactive mode, or specify a command.[/yellow]")
            print(ctx.get_help())


def interactive_loop(ctx: typer.Context):
    """
    Run the interactive command loop.

    :param ctx: The Typer context object
    :type ctx: typer.Context
    :except KeyboardInterrupt: User interrupts the loop
    :except Exception: Error executing command
    """
    print("\n[bold cyan]Interactive Mode Started[/bold cyan]")
    print("[dim]Type 'help' for available commands or 'exit'/'quit' to leave.[/dim]\n")
    
    while True:
        try:
            # Get user input
            user_input = Prompt.ask("[bold blue]DiMMS[/bold blue]", default="").strip()
            
            if not user_input:
                continue
                
            # Handle exit commands
            if user_input.lower() in ['exit', 'quit', 'bye,' 'q']:
                print("[green]Goodbye![/green]")
                break
                
            # Handle help command
            if user_input.lower() in ['help', 'h']:
                typer.echo(ctx.get_help())
                continue
                
            # Parse and execute command
            exec_cmd(user_input)
            
        except KeyboardInterrupt:
            print("\n[yellow]Use 'exit' or 'quit' to leave.[/yellow]")
        except Exception as e:
            print(f"[red]Error: {e}[/red]")


def exec_cmd(user_input: str):
    """
    Parse and execute a command from user input.
    
    :param user_input: The command string entered by the user
    :type user_input: str
    """
    try:
        # Split the input into command and arguments
        parts = shlex.split(user_input)
        if not parts:
            return
            
        command = parts[0].lower().replace('-', '_')  # Convert kebab-case to snake_case
        args = parts[1:]
        
        # Execute the appropriate command
        if command == "hello":
            name = args[0] if args else "world"
            hello(name)
        elif command == "search_artists":
            if not args:
                print("[red]Error: Artist name is required[/red]")
                print("[dim]Usage: search-artists <artist_name>[/dim]")
                return
            search_artists(" ".join(args))
        else:
            print(f"[red]Unknown command: {command}[/red]")
            print("[dim]Type 'help' for available commands.[/dim]")
            
    except Exception as e:
        print(f"[red]Error executing command: {e}[/red]")


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
    print("Total Results: ", DISCOGS_DATA["total_results"])


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

            for result in data.get("results", [])[:10]:  # Show first 6
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


@app.command()
def get_albums_by_artist(artist_id: int):
    """
    Get albums by artist ID.

    :param artist_id: The ID of the artist to get albums for
    :type artist_id: int
    """
    DISCOGS_DATA = get_albums_data(artist_id)

    table = Table(title=f"Albums for Artist ID: {artist_id}")
    table.add_column("No.", justify="right", style="green", no_wrap=True)
    table.add_column("Title", justify="right", style="cyan", no_wrap=True)
    table.add_column("ID", justify="left", style="magenta", no_wrap=True)
    
    # for album in DISCOGS_DATA["albums"]:
    #     table.add_row(
    #         album["title"],
    #         str(album["id"]),
    #     )

    for i, (cmd, desc) in enumerate(DISCOGS_DATA["albums"], 1):
        table.add_row(str(i), cmd, desc)


    console.print(table)
    print("Total Results: ", DISCOGS_DATA["total_results"])


def get_albums_data(artist_id: int) -> Dict[str, Any]:
    """
    Get albums by artist ID using the Discogs API.

    :param artist_id: The ID of the artist to get albums for
    :type artist_id: int
    :returns: A dictionary containing the found albums data
    :rtype: Dict[str, Any]
    """
    result_dict = {}
    try:
        headers = get_discogs_headers()
        params = {"artist": artist_id}

        response = CACHED_SESSION.get(
            f"{BASE_URL}/database/search", headers=headers, params=params
        )

        if response.status_code == 200:
            data = response.json()
            result_dict["total_results"] = data.get("pagination", {}).get("items", 0)
            result_dict["albums"] = []

            for result in data.get("results", [])[:10]:
                album_info = {
                    "title": result.get("title"),
                    "id": result.get("id"),
                    "uri": result.get("uri"),
                }
                result_dict["albums"].append(album_info)
        else:
            result_dict["error"] = f"Error: {response.status_code}"
    except Exception as e:
        logger.error(f"Search error: {e}")
        result_dict["error"] = str(e)
        
    return result_dict


@app.command()
def help():
    """Show numbered help menu."""
    table = Table(title="Available Commands")
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Command", style="green")
    table.add_column("Description", style="white")
    
    commands = [
        ("search-artists", "Search for an artist by name"),
        ("hello", "Say hello to someone"),
        ("list-albums", "List albums for a specific artist"),
    ]
    
    for i, (cmd, desc) in enumerate(commands, 1):
        table.add_row(str(i), cmd, desc)
    
    console.print(table)

if __name__ == "__main__":
    app()
