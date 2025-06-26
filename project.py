import typer
import sys
import os
import csv
import logging
import shlex
import ast
from typing import Dict, List, Any
from requests_cache import CachedSession
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory

# Global Variable
BASE_URL: str = "https://api.discogs.com"
CACHED_SESSION: CachedSession = CachedSession(
    "discogs_api_cache", backend="sqlite", expire_after=1800
)
DISCOGS_DATA: Dict[str, Any] = {}
DISCOGS_TOKEN: str | None = os.getenv("DISCOGS_TOKEN")
INTERACTIVE_MODE: bool = False

# Init Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger: logging.Logger = logging.getLogger(__name__)

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
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Run in interactive mode"
    ),
) -> None:
    """
    Main entry point for DiMMS-CLI.

    :param ctx: The Typer context object
    :type ctx: typer.Context
    :param interactive: Whether to run in interactive mode
    :type interactive: bool
    """
    global INTERACTIVE_MODE
    INTERACTIVE_MODE = interactive

    print("[bold green]Discogs Music Metadata Search[/bold green]")

    # Test authentication on startup
    if DISCOGS_TOKEN:
        if test_authentication():
            print("[green]✓ Authentication successful[/green]")
        else:
            print("[red]✗ Authentication failed[/red]")
            print("Please check your DISCOGS_TOKEN environment variable")
            sys.exit(1)
    else:
        print(
            "[yellow]⚠  No DISCOGS_TOKEN found.\nPlease set your Personal Access Token.[/yellow]"
        )
        sys.exit(1)

    # If no subcommand is invoked and interactive mode is requested, start the loop
    if ctx.invoked_subcommand is None:
        if interactive:
            interactive_loop(ctx)
        else:
            # Show help if not in interactive mode and no command given
            print(
                "\n[yellow]Use --interactive or -i for interactive mode, or specify a command.[/yellow]"
            )
            print(ctx.get_help())


def interactive_loop(ctx: typer.Context) -> None:
    """
    Run the interactive command loop with autocomplete and history.

    :param ctx: The Typer context object
    :type ctx: typer.Context
    :return: None
    """
    print("\n[bold cyan]Interactive Mode Started[/bold cyan]")
    print("[dim]Type 'help' for available commands[/dim]")
    print("[dim]or 'exit'/'quit'/'bye'/'q' to leave.[/dim]\n")

    # Usage
    command_function_names = get_app_command_functions("project.py")
    command_function_names += ["bye", "q", "exit", "quit"]
    # Set up command completion
    command_completer = WordCompleter(command_function_names, ignore_case=True)

    # Set up history
    history = InMemoryHistory()

    while True:
        try:
            # Get user input with autocomplete and history
            user_input = prompt(
                [
                    ("bold fg:ansiblue", "DiMMS "),
                    ("bold fg:ansigreen", "()"),
                    ("", ": "),
                ],
                completer=command_completer,
                history=history,
                complete_while_typing=True,
            ).strip()

            if not user_input:
                continue

            # Handle exit commands
            if user_input.lower() in ["bye", "q"]:
                print("[bold green]Goodbye![/bold green]")
                break

            # Handle help command
            if user_input.lower() in ["help", "h"]:
                typer.echo(ctx.get_help())
                continue

            # Parse and execute command
            exec_cmd(user_input)

        except KeyboardInterrupt:
            print("\nUse 'bye'/'q' to leave.")
        except EOFError:
            print("[bold green]Goodbye![/bold green]")
            break
        except Exception as e:
            print(f"Error: {e}")


def exec_cmd(user_input: str) -> None:
    """
    Parse and execute a command from user input.

    :param user_input: The command string entered by the user
    :type user_input: str
    :return: None
    """
    try:
        # Split the input into command and arguments
        parts = shlex.split(user_input)
        if not parts:
            return

        print(user_input)
        command = parts[0].lower().replace("-", "_")  # Convert kebab-case to snake_case
        args = parts[1:]

        # Execute the appropriate command
        if command == "search_artists":
            if not args:
                print("[red]Error: Artist name is required[/red]")
                print("[dim]Usage: search-artists <artist_name>[/dim]")
                return
            search_artists(" ".join(args))
        elif command == "list_albums":
            list_albums(int(args[0]))
        elif command == "write_last_search_to_file":
            write_last_search_to_file()
        elif command == "dump_all_data":
            # Parse optional arguments for dump command
            filename = "complete_dump.csv"
            separate_files = False

            for i, arg in enumerate(args):
                if arg in ["-f", "--file"] and i + 1 < len(args):
                    filename = args[i + 1]
                elif arg in ["-s", "--separate"]:
                    separate_files = True

            dump_all_data(filename, separate_files)
        else:
            print(f"[red]Unknown command: {command}[/red]")
            print("[dim]Type 'help' for available commands.[/dim]")

    except Exception as e:
        print(f"[red]Error executing command: {e}[/red]")


# Authentication
def get_discogs_headers() -> dict:
    """
    Get headers for Discogs API requests.

    :raise ValueError: If DISCOGS_TOKEN environment variable is not set
    :return: A dictionary of headers
    :rtype: dict
    """
    if not DISCOGS_TOKEN:
        raise ValueError("DISCOGS_TOKEN environment variable not set")

    return {
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": "DiMMS-CLI/1.0",
    }


def test_authentication() -> bool:
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
@app.command()
def search_artists(artist_name: str) -> None:
    """
    Search for an artist by name.

    :param artist_name: The name of the artist to search for
    :type artist_name: str
    :except Exception: Search error
    """
    global DISCOGS_DATA
    if "artists" not in DISCOGS_DATA:
        DISCOGS_DATA["artists"] = {}

    search_results = get_artists_data(artist_name)

    # Initialize the artist entry with search results and empty albums
    DISCOGS_DATA["artists"][artist_name.lower()] = {
        "search_results": search_results,
        "albums": {},
    }

    # Keep track of the last searched artist
    DISCOGS_DATA["last_search"] = {
        "type": "artists",
        "key": artist_name.lower(),
        "data": search_results,
    }

    table = Table(title=f"Search Results for: {artist_name}")
    table.add_column("Name", justify="right", style="cyan", no_wrap=True)
    table.add_column("ID", justify="left", style="magenta", no_wrap=True)

    for artist in search_results["artists"]:
        table.add_row(
            artist["title"],
            str(artist["id"]),
        )

    console.print(table)
    print("Total Results: ", search_results["total_artist"])


def get_artists_data(artist_name: str) -> Dict[str, Any]:
    """
    Search for artists by name using the Discogs API.

    Performs a search query against the Discogs database to find artists matching
    the provided name. Returns up to 10 results with artist information including
    title, ID, and URI.

    :param artist_name: The name of the artist to search for. Can be a partial
    or full artist name.
    :type artist_name: str
    :returns: A dictionary containing the found artists data
    :rtype: Dict[str, Any]
    :except Exception: Search error
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
            result_dict["total_artist"] = data.get("pagination", {}).get("items", 0)
            result_dict["artists"] = []

            for result in data.get("results", [])[:]:
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
def list_albums(artist_id: int) -> None:
    """
    Get albums by artist ID and store them under the appropriate artist.

    :param artist_id: The ID of the artist to get albums for
    :type artist_id: int
    """
    global DISCOGS_DATA

    # Get release data
    release_data = get_release_data(artist_id)

    # Find which artist this ID belongs to
    target_artist_key = None
    for artist_key, artist_data in DISCOGS_DATA.get("artists", {}).items():
        if "search_results" in artist_data:
            for artist in artist_data["search_results"].get("artists", []):
                if artist["id"] == artist_id:
                    target_artist_key = artist_key
                    break
        if target_artist_key:
            break

    # If no matching artist found, create a generic entry
    if not target_artist_key:
        if "artists" not in DISCOGS_DATA:
            DISCOGS_DATA["artists"] = {}
        target_artist_key = f"artist_{artist_id}"
        DISCOGS_DATA["artists"][target_artist_key] = {
            "search_results": {"artists": [], "total_artist": 0},
            "albums": {},
        }

    # Store albums under the artist's albums section
    DISCOGS_DATA["artists"][target_artist_key]["albums"][str(artist_id)] = release_data

    # Update last search
    DISCOGS_DATA["last_search"] = {
        "type": "albums",
        "key": target_artist_key,
        "artist_id": str(artist_id),
        "data": release_data,
    }

    table = Table(title=f"Albums for Artist ID: {artist_id}")
    table.add_column("Title", justify="right", style="cyan", no_wrap=True)
    table.add_column("Year", justify="left", style="yellow", no_wrap=True)
    table.add_column("ID", justify="left", style="magenta", no_wrap=True)

    for release in release_data["releases"]:
        table.add_row(
            release["title"],
            str(release["year"]),
            str(release["id"]),
        )

    console.print(table)
    print("Total Results: ", release_data["total_releases"])


def get_release_data(artist_id: int) -> Dict[str, Any]:
    """
    Get releases by artist ID using the Discogs API.

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
            f"{BASE_URL}/artists/{artist_id}/releases", headers=headers, params=params
        )

        if response.status_code == 200:
            data = response.json()
            # print(data)
            result_dict["total_releases"] = data.get("pagination", {}).get("items", 0)
            result_dict["releases"] = []

            for result in data.get("releases", [])[:]:
                release_info = {
                    "id": result.get("id"),
                    "artist": result.get("artist"),
                    "title": result.get("title"),
                    "year": result.get("year"),
                }
                result_dict["releases"].append(release_info)
        else:
            result_dict["error"] = f"Error: {response.status_code}"
    except Exception as e:
        logger.error(f"Search error: {e}")
        result_dict["error"] = str(e)

    return result_dict


@app.command()
def write_last_search_to_file():
    """
    Write data to a CSV file using the last search results.
    """
    if not DISCOGS_DATA or "last_search" not in DISCOGS_DATA:
        print(
            "[red]No recent search data available. Please search for artists or albums first.[/red]"
        )
        return

    last_search = DISCOGS_DATA["last_search"]

    if last_search["type"] == "artists":
        # Write artist data
        if "artists" not in last_search["data"]:
            print("[red]No artist data in last search.[/red]")
            return

        fieldnames = ["title", "id", "uri"]
        filename = f"artists_{last_search['key']}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(last_search["data"]["artists"])

        print(
            f"[green]Successfully wrote {len(last_search['data']['artists'])} artists to {filename}[/green]"
        )

    elif last_search["type"] == "albums":
        # Write album data
        if "releases" not in last_search["data"]:
            print("[red]No album data in last search.[/red]")
            return

        fieldnames = ["title", "year", "id", "artist"]
        filename = f"albums_{last_search['key']}_{last_search['artist_id']}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(last_search["data"]["releases"])

        print(
            f"[green]Successfully wrote {len(last_search['data']['releases'])} albums to {filename}[/green]"
        )


@app.command()
def dump_all_data(
    filename: str = typer.Option(
        "complete_dump.csv", "--file", "-f", help="Output CSV filename"
    ),
    separate_files: bool = typer.Option(
        False, "--separate", "-s", help="Create separate files for artists and albums"
    ),
):
    """
    Dump all stored data (artists and albums) from the program's lifetime to CSV file(s).

    :param filename: The base filename for the dump
    :type filename: str
    :param separate_files: Whether to create separate files for artists and albums
    :type separate_files: bool
    """
    if not DISCOGS_DATA or "artists" not in DISCOGS_DATA:
        print(
            "[red]No data available to dump. Please perform some searches first.[/red]"
        )
        return

    try:
        if separate_files:
            # Create separate files for artists and albums
            _dump_artists_data(f"artists_{filename}")
            _dump_albums_data(f"albums_{filename}")
        else:
            # Create a single comprehensive file
            _dump_comprehensive_data(filename)

    except Exception as e:
        print(f"[red]Error during dump: {e}[/red]")


def _dump_artists_data(filename: str) -> None:
    """
    Dump all artist search results to a CSV file.

    :param filename: Output filename
    :type filename: str
    """
    artists_data = []

    for artist_key, artist_info in DISCOGS_DATA["artists"].items():
        if (
            "search_results" in artist_info
            and "artists" in artist_info["search_results"]
        ):
            for artist in artist_info["search_results"]["artists"]:
                artists_data.append(
                    {
                        "search_term": artist_key,
                        "title": artist.get("title", ""),
                        "id": artist.get("id", ""),
                        "uri": artist.get("uri", ""),
                        "total_results": artist_info["search_results"].get(
                            "total_artist", 0
                        ),
                    }
                )

    if artists_data:
        fieldnames = ["search_term", "title", "id", "uri", "total_results"]

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(artists_data)

        print(
            f"[green]Successfully wrote {len(artists_data)} artist records to {filename}[/green]"
        )
    else:
        print("[yellow]No artist data found to write.[/yellow]")


def _dump_albums_data(filename: str) -> None:
    """
    Dump all album/release data to a CSV file.

    :param filename: Output filename
    :type filename: str
    """
    albums_data = []

    for artist_key, artist_info in DISCOGS_DATA["artists"].items():
        if "albums" in artist_info:
            for artist_id, album_info in artist_info["albums"].items():
                if "releases" in album_info:
                    for release in album_info["releases"]:
                        albums_data.append(
                            {
                                "search_term": artist_key,
                                "artist_id": artist_id,
                                "release_id": release.get("id", ""),
                                "artist_name": release.get("artist", ""),
                                "title": release.get("title", ""),
                                "year": release.get("year", ""),
                                "total_releases": album_info.get("total_releases", 0),
                            }
                        )

    if albums_data:
        fieldnames = [
            "search_term",
            "artist_id",
            "release_id",
            "artist_name",
            "title",
            "year",
            "total_releases",
        ]

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(albums_data)

        print(
            f"[green]Successfully wrote {len(albums_data)} album records to {filename}[/green]"
        )
    else:
        print("[yellow]No album data found to write.[/yellow]")


def _dump_comprehensive_data(filename: str) -> None:
    """
    Dump all data in a single comprehensive CSV file.

    :param filename: Output filename
    :type filename: str
    """
    all_data = []

    # Process all artists and their albums
    for artist_key, artist_info in DISCOGS_DATA["artists"].items():
        # Add artist search results
        if (
            "search_results" in artist_info
            and "artists" in artist_info["search_results"]
        ):
            for artist in artist_info["search_results"]["artists"]:
                all_data.append(
                    {
                        "data_type": "artist",
                        "search_term": artist_key,
                        "artist_id": artist.get("id", ""),
                        "artist_name": artist.get("title", ""),
                        "title": artist.get("title", ""),
                        "id": artist.get("id", ""),
                        "uri": artist.get("uri", ""),
                        "year": "",
                        "release_id": "",
                        "total_count": artist_info["search_results"].get(
                            "total_artist", 0
                        ),
                    }
                )

        # Add album/release data
        if "albums" in artist_info:
            for queried_artist_id, album_info in artist_info["albums"].items():
                if "releases" in album_info:
                    for release in album_info["releases"]:
                        all_data.append(
                            {
                                "data_type": "album",
                                "search_term": artist_key,
                                "artist_id": queried_artist_id,
                                "artist_name": release.get("artist", ""),
                                "title": release.get("title", ""),
                                "id": release.get("id", ""),
                                "uri": "",
                                "year": release.get("year", ""),
                                "release_id": release.get("id", ""),
                                "total_count": album_info.get("total_releases", 0),
                            }
                        )

    if all_data:
        fieldnames = [
            "data_type",
            "search_term",
            "artist_id",
            "artist_name",
            "title",
            "id",
            "uri",
            "year",
            "release_id",
            "total_count",
        ]

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)

        print(
            f"[green]Successfully wrote {len(all_data)} total records to {filename}[/green]"
        )

        # Print summary
        artist_count = len([d for d in all_data if d["data_type"] == "artist"])
        album_count = len([d for d in all_data if d["data_type"] == "album"])
        print(f"[cyan]Summary: {artist_count} artists, {album_count} albums[/cyan]")
    else:
        print("[yellow]No data found to write.[/yellow]")


def get_app_command_functions(filename: str) -> List[str]:
    """
    Extract all app.command() names from a file

    :param filename: The name of the file to read
    :type filename: str
    :return: A list of command names
    :rtype: List[str]
    """
    with open(filename, "r") as file:
        tree = ast.parse(file.read())

    command_functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if function has @app.command() decorator
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "app"
                    and decorator.func.attr == "command"
                ):
                    command_functions.append(node.name)
                    break

    return command_functions


if __name__ == "__main__":
    app()
