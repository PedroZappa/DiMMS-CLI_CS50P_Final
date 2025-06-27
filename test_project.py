import typer
import pytest
import ast
from unittest.mock import patch, mock_open, MagicMock
from typer.testing import CliRunner
from project import dump_all_data
from project import write_last_search_to_file
from project import get_app_command_functions
from project import app

runner = CliRunner()


def test_app():
    result = runner.invoke(app, ["search-artists", "Muse"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["list-albums", "1"])
    assert result.exit_code == 0

    result = runner.invoke(app, [""])
    assert result.exit_code == 2


class TestWriteLastSearchToFile:

    @patch("project.print")
    @patch("project.DISCOGS_DATA", {})
    def test_write_last_search_no_data_available(self, mock_print):
        """Test behavior when no DISCOGS_DATA is available."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        mock_print.assert_called_once_with(
            "[red]No recent search data available. Please search for artists or albums first.[/red]"
        )
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project.DISCOGS_DATA", {"other_key": "value"})
    def test_write_last_search_missing_last_search_key(self, mock_print):
        """Test behavior when DISCOGS_DATA exists but missing 'last_search' key."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        mock_print.assert_called_once_with(
            "[red]No recent search data available. Please search for artists or albums first.[/red]"
        )
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project.csv.DictWriter")
    @patch("project.open", new_callable=mock_open)
    @patch(
        "project.DISCOGS_DATA",
        {
            "last_search": {
                "type": "artists",
                "key": "test_artist",
                "data": {
                    "artists": [
                        {"title": "Artist 1", "id": "123", "uri": "/artist/123"},
                        {"title": "Artist 2", "id": "456", "uri": "/artist/456"},
                    ]
                },
            }
        },
    )
    def test_write_last_search_artists_success(
        self, mock_file, mock_dict_writer, mock_print
    ):
        """Test successful writing of artist search results."""
        mock_writer_instance = MagicMock()
        mock_dict_writer.return_value = mock_writer_instance

        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        # Verify file was opened correctly
        mock_file.assert_called_once_with(
            "artists_test_artist.csv", "w", newline="", encoding="utf-8"
        )

        # Verify CSV writer operations
        mock_dict_writer.assert_called_once_with(
            mock_file.return_value.__enter__.return_value,
            fieldnames=["title", "id", "uri"],
        )
        mock_writer_instance.writeheader.assert_called_once()
        mock_writer_instance.writerows.assert_called_once_with(
            [
                {"title": "Artist 1", "id": "123", "uri": "/artist/123"},
                {"title": "Artist 2", "id": "456", "uri": "/artist/456"},
            ]
        )

        # Verify success message
        mock_print.assert_called_once_with(
            "[green]Successfully wrote 2 artists to artists_test_artist.csv[/green]"
        )
        assert result.exit_code == 0

    @patch("project.print")
    @patch(
        "project.DISCOGS_DATA",
        {"last_search": {"type": "artists", "key": "test_artist", "data": {}}},
    )
    def test_write_last_search_artists_no_data(self, mock_print):
        """Test behavior when artist search has no artist data."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        mock_print.assert_called_once_with("[red]No artist data in last search.[/red]")
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project.csv.DictWriter")
    @patch("project.open", new_callable=mock_open)
    @patch(
        "project.DISCOGS_DATA",
        {
            "last_search": {
                "type": "albums",
                "key": "test_album",
                "artist_id": "789",
                "data": {
                    "releases": [
                        {
                            "title": "Album 1",
                            "year": "2020",
                            "id": "111",
                            "artist": "Artist A",
                        },
                        {
                            "title": "Album 2",
                            "year": "2021",
                            "id": "222",
                            "artist": "Artist B",
                        },
                    ]
                },
            }
        },
    )
    def test_write_last_search_albums_success(
        self, mock_file, mock_dict_writer, mock_print
    ):
        """Test successful writing of album search results."""
        mock_writer_instance = MagicMock()
        mock_dict_writer.return_value = mock_writer_instance

        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        # Verify file was opened correctly
        mock_file.assert_called_once_with(
            "albums_test_album_789.csv", "w", newline="", encoding="utf-8"
        )

        # Verify CSV writer operations
        mock_dict_writer.assert_called_once_with(
            mock_file.return_value.__enter__.return_value,
            fieldnames=["title", "year", "id", "artist"],
        )
        mock_writer_instance.writeheader.assert_called_once()
        mock_writer_instance.writerows.assert_called_once_with(
            [
                {"title": "Album 1", "year": "2020", "id": "111", "artist": "Artist A"},
                {"title": "Album 2", "year": "2021", "id": "222", "artist": "Artist B"},
            ]
        )

        # Verify success message
        mock_print.assert_called_once_with(
            "[green]Successfully wrote 2 albums to albums_test_album_789.csv[/green]"
        )
        assert result.exit_code == 0

    @patch("project.print")
    @patch(
        "project.DISCOGS_DATA",
        {
            "last_search": {
                "type": "albums",
                "key": "test_album",
                "artist_id": "789",
                "data": {},
            }
        },
    )
    def test_write_last_search_albums_no_data(self, mock_print):
        """Test behavior when album search has no release data."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        mock_print.assert_called_once_with("[red]No album data in last search.[/red]")
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project.csv.DictWriter")
    @patch("project.open", new_callable=mock_open)
    @patch(
        "project.DISCOGS_DATA",
        {
            "last_search": {
                "type": "artists",
                "key": "test_with_special_chars",
                "data": {
                    "artists": [
                        {
                            "title": "Artíst wîth Spëcial Chärs",
                            "id": "999",
                            "uri": "/artist/999",
                        }
                    ]
                },
            }
        },
    )
    def test_write_last_search_artists_with_special_characters(
        self, mock_file, mock_dict_writer, mock_print
    ):
        """Test writing artist data with special characters."""
        mock_writer_instance = MagicMock()
        mock_dict_writer.return_value = mock_writer_instance

        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        # Verify file was opened with UTF-8 encoding
        mock_file.assert_called_once_with(
            "artists_test_with_special_chars.csv", "w", newline="", encoding="utf-8"
        )

        # Verify success message
        mock_print.assert_called_once_with(
            "[green]Successfully wrote 1 artists to artists_test_with_special_chars.csv[/green]"
        )
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project.csv.DictWriter")
    @patch("project.open", new_callable=mock_open)
    @patch(
        "project.DISCOGS_DATA",
        {
            "last_search": {
                "type": "albums",
                "key": "test_album_special",
                "artist_id": "123",
                "data": {
                    "releases": [
                        {
                            "title": "Albüm wîth Spëcial Chärs",
                            "year": "2022",
                            "id": "888",
                            "artist": "Artíst",
                        }
                    ]
                },
            }
        },
    )
    def test_write_last_search_albums_with_special_characters(
        self, mock_file, mock_dict_writer, mock_print
    ):
        """Test writing album data with special characters."""
        mock_writer_instance = MagicMock()
        mock_dict_writer.return_value = mock_writer_instance

        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        # Verify file was opened with UTF-8 encoding
        mock_file.assert_called_once_with(
            "albums_test_album_special_123.csv", "w", newline="", encoding="utf-8"
        )

        # Verify success message
        mock_print.assert_called_once_with(
            "[green]Successfully wrote 1 albums to albums_test_album_special_123.csv[/green]"
        )
        assert result.exit_code == 0

    # Direct function call tests
    @patch("project.print")
    @patch("project.csv.DictWriter")
    @patch("project.open", new_callable=mock_open)
    @patch(
        "project.DISCOGS_DATA",
        {
            "last_search": {
                "type": "artists",
                "key": "direct_test",
                "data": {
                    "artists": [
                        {
                            "title": "Direct Test Artist",
                            "id": "999",
                            "uri": "/artist/999",
                        }
                    ]
                },
            }
        },
    )
    def test_write_last_search_direct_function_call(
        self, mock_file, mock_dict_writer, mock_print
    ):
        """Test calling the function directly."""
        mock_writer_instance = MagicMock()
        mock_dict_writer.return_value = mock_writer_instance

        # Call function directly
        write_last_search_to_file()

        mock_print.assert_called_once_with(
            "[green]Successfully wrote 1 artists to artists_direct_test.csv[/green]"
        )

    @patch("project.print")
    @patch(
        "project.DISCOGS_DATA",
        {"last_search": {"type": "unknown_type", "key": "test", "data": {}}},
    )
    def test_write_last_search_unknown_type(self, mock_print):
        """Test behavior with unknown search type."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        # Function should complete without error but no output for unknown type
        mock_print.assert_not_called()
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project.csv.DictWriter")
    @patch("project.open", new_callable=mock_open)
    @patch(
        "project.DISCOGS_DATA",
        {
            "last_search": {
                "type": "artists",
                "key": "empty_list",
                "data": {"artists": []},
            }
        },
    )
    def test_write_last_search_empty_artists_list(
        self, mock_file, mock_dict_writer, mock_print
    ):
        """Test writing empty artists list."""
        mock_writer_instance = MagicMock()
        mock_dict_writer.return_value = mock_writer_instance

        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        mock_writer_instance.writerows.assert_called_once_with([])
        mock_print.assert_called_once_with(
            "[green]Successfully wrote 0 artists to artists_empty_list.csv[/green]"
        )
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project.csv.DictWriter")
    @patch("project.open", new_callable=mock_open)
    @patch(
        "project.DISCOGS_DATA",
        {
            "last_search": {
                "type": "albums",
                "key": "empty_albums",
                "artist_id": "999",
                "data": {"releases": []},
            }
        },
    )
    def test_write_last_search_empty_albums_list(
        self, mock_file, mock_dict_writer, mock_print
    ):
        """Test writing empty albums list."""
        mock_writer_instance = MagicMock()
        mock_dict_writer.return_value = mock_writer_instance

        runner = CliRunner()
        app = typer.Typer()
        app.command()(write_last_search_to_file)

        result = runner.invoke(app, [])

        mock_writer_instance.writerows.assert_called_once_with([])
        mock_print.assert_called_once_with(
            "[green]Successfully wrote 0 albums to albums_empty_albums_999.csv[/green]"
        )
        assert result.exit_code == 0


class TestDumpAllData:

    @patch("project.print")
    @patch("project.DISCOGS_DATA", {})
    def test_dump_all_data_no_data_available(self, mock_print):
        """Test behavior when no data is available to dump."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(dump_all_data)

        result = runner.invoke(app, [])

        mock_print.assert_called_once_with(
            "[red]No data available to dump. Please perform some searches first.[/red]"
        )
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project.DISCOGS_DATA", {"other_key": "value"})
    def test_dump_all_data_missing_artists_key(self, mock_print):
        """Test behavior when DISCOGS_DATA exists but missing 'artists' key."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(dump_all_data)

        result = runner.invoke(app, [])

        mock_print.assert_called_once_with(
            "[red]No data available to dump. Please perform some searches first.[/red]"
        )
        assert result.exit_code == 0

    @patch("project._dump_comprehensive_data")
    @patch("project.DISCOGS_DATA", {"artists": {"artist1": "data"}})
    def test_dump_all_data_single_file_default_filename(self, mock_dump_comprehensive):
        """Test dumping to single file with default filename."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(dump_all_data)

        result = runner.invoke(app, [])

        mock_dump_comprehensive.assert_called_once_with("complete_dump.csv")
        assert result.exit_code == 0

    @patch("project._dump_comprehensive_data")
    @patch("project.DISCOGS_DATA", {"artists": {"artist1": "data"}})
    def test_dump_all_data_single_file_custom_filename(self, mock_dump_comprehensive):
        """Test dumping to single file with custom filename."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(dump_all_data)

        result = runner.invoke(app, ["--file", "custom_dump.csv"])

        mock_dump_comprehensive.assert_called_once_with("custom_dump.csv")
        assert result.exit_code == 0

    @patch("project._dump_albums_data")
    @patch("project._dump_artists_data")
    @patch("project.DISCOGS_DATA", {"artists": {"artist1": "data"}})
    def test_dump_all_data_separate_files(self, mock_dump_artists, mock_dump_albums):
        """Test dumping to separate files for artists and albums."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(dump_all_data)

        result = runner.invoke(app, ["--separate", "--file", "test_dump.csv"])

        mock_dump_artists.assert_called_once_with("artists_test_dump.csv")
        mock_dump_albums.assert_called_once_with("albums_test_dump.csv")
        assert result.exit_code == 0

    @patch("project._dump_albums_data")
    @patch("project._dump_artists_data")
    @patch("project.DISCOGS_DATA", {"artists": {"artist1": "data"}})
    def test_dump_all_data_separate_files_short_flags(
        self, mock_dump_artists, mock_dump_albums
    ):
        """Test dumping to separate files using short flags."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(dump_all_data)

        result = runner.invoke(app, ["-s", "-f", "short_dump.csv"])

        mock_dump_artists.assert_called_once_with("artists_short_dump.csv")
        mock_dump_albums.assert_called_once_with("albums_short_dump.csv")
        assert result.exit_code == 0

    @patch("project.print")
    @patch(
        "project._dump_comprehensive_data", side_effect=Exception("File write error")
    )
    @patch("project.DISCOGS_DATA", {"artists": {"artist1": "data"}})
    def test_dump_all_data_exception_handling_single_file(
        self, mock_dump_comprehensive, mock_print
    ):
        """Test exception handling when dumping to single file fails."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(dump_all_data)

        result = runner.invoke(app, [])

        mock_print.assert_called_once_with(
            "[red]Error during dump: File write error[/red]"
        )
        assert result.exit_code == 0

    @patch("project.print")
    @patch("project._dump_albums_data", side_effect=Exception("Albums dump error"))
    @patch("project._dump_artists_data")
    @patch("project.DISCOGS_DATA", {"artists": {"artist1": "data"}})
    def test_dump_all_data_exception_handling_separate_files(
        self, mock_dump_artists, mock_dump_albums, mock_print
    ):
        """Test exception handling when dumping separate files fails."""
        runner = CliRunner()
        app = typer.Typer()
        app.command()(dump_all_data)

        result = runner.invoke(app, ["--separate"])

        mock_print.assert_called_once_with(
            "[red]Error during dump: Albums dump error[/red]"
        )
        assert result.exit_code == 0

    # Alternative approach: Testing the function directly without CliRunner
    @patch("project.print")
    @patch("project._dump_comprehensive_data")
    @patch("project.DISCOGS_DATA", {"artists": {"artist1": "data"}})
    def test_dump_all_data_direct_function_call(
        self, mock_dump_comprehensive, mock_print
    ):
        """Test calling the function directly with parameters."""
        # Call the function directly
        dump_all_data(filename="direct_test.csv", separate_files=False)

        mock_dump_comprehensive.assert_called_once_with("direct_test.csv")
        mock_print.assert_not_called()

    @patch("project._dump_albums_data")
    @patch("project._dump_artists_data")
    @patch("project.DISCOGS_DATA", {"artists": {"artist1": "data"}})
    def test_dump_all_data_direct_separate_files(
        self, mock_dump_artists, mock_dump_albums
    ):
        """Test calling the function directly with separate_files=True."""
        dump_all_data(filename="direct_separate.csv", separate_files=True)

        mock_dump_artists.assert_called_once_with("artists_direct_separate.csv")
        mock_dump_albums.assert_called_once_with("albums_direct_separate.csv")


class TestGetAppCommandFunctions:

    def test_single_app_command_function(self):
        """Test extracting a single function with @app.command() decorator."""
        file_content = """
@app.command()
def search_artists():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["search_artists"]

    def test_multiple_app_command_functions(self):
        """Test extracting multiple functions with @app.command() decorator."""
        file_content = """
@app.command()
def search_artists():
    pass

@app.command()
def list_albums():
    pass

@app.command()
def dump_data():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["search_artists", "list_albums", "dump_data"]

    def test_mixed_functions_with_and_without_decorator(self):
        """Test file with mix of decorated and non-decorated functions."""
        file_content = """
@app.command()
def search_artists():
    pass

def helper_function():
    pass

@app.command()
def list_albums():
    pass

def another_helper():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["search_artists", "list_albums"]

    def test_functions_with_other_decorators(self):
        """Test functions with decorators other than @app.command()."""
        file_content = """
@pytest.fixture
def test_fixture():
    pass

@staticmethod
def static_method():
    pass

@app.command()
def valid_command():
    pass

@some_other_decorator
def decorated_function():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["valid_command"]

    def test_functions_with_multiple_decorators(self):
        """Test functions with multiple decorators including @app.command()."""
        file_content = """
@some_decorator
@app.command()
@another_decorator
def multi_decorated_function():
    pass

@app.command()
@pytest.fixture
def command_with_fixture():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["multi_decorated_function", "command_with_fixture"]

    def test_app_command_with_arguments(self):
        """Test @app.command() decorator with arguments."""
        file_content = """
@app.command(name="custom-name")
def search_with_custom_name():
    pass

@app.command(help="Help text")
def command_with_help():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["search_with_custom_name", "command_with_help"]

    def test_similar_but_different_decorators(self):
        """Test decorators that look similar but are not @app.command()."""
        file_content = """
@other_app.command()
def wrong_app():
    pass

@app.other_method()
def wrong_method():
    pass

@command()
def missing_app():
    pass

@app.command()
def correct_command():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["correct_command"]

    def test_empty_file(self):
        """Test behavior with empty file."""
        with patch("builtins.open", mock_open(read_data="")):
            result = get_app_command_functions("empty_file.py")
            assert result == []

    def test_file_with_only_comments_and_imports(self):
        """Test file with no functions."""
        file_content = """
# This is a comment
import os
import sys

# Another comment
from typing import List
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == []


    def test_file_not_found_error(self):
        """Test behavior when file does not exist."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                get_app_command_functions("nonexistent_file.py")

    def test_permission_error(self):
        """Test behavior when file cannot be read due to permissions."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                get_app_command_functions("restricted_file.py")

    def test_syntax_error_in_file(self):
        """Test behavior when file contains syntax errors."""
        file_content = """
@app.command()
def invalid_syntax(
    # Missing closing parenthesis and colon
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            with pytest.raises(SyntaxError):
                get_app_command_functions("invalid_syntax_file.py")

    @pytest.mark.parametrize(
        "filename,expected_count",
        [
            ("single_command.py", 1),
            ("multiple_commands.py", 3),
            ("no_commands.py", 0),
            ("mixed_file.py", 2),
        ],
    )
    def test_different_files_parametrized(self, filename, expected_count):
        """Test function with different files using parametrize."""
        # Mock different file contents based on filename
        file_contents = {
            "single_command.py": "@app.command()\ndef single(): pass",
            "multiple_commands.py": "@app.command()\ndef first(): pass\n@app.command()\ndef second(): pass\n@app.command()\ndef third(): pass",
            "no_commands.py": "def regular(): pass\ndef another(): pass",
            "mixed_file.py": "@app.command()\ndef cmd1(): pass\ndef regular(): pass\n@app.command()\ndef cmd2(): pass",
        }

        with patch("builtins.open", mock_open(read_data=file_contents[filename])):
            result = get_app_command_functions(filename)
            assert len(result) == expected_count

    def test_decorator_without_parentheses_not_matched(self):
        """Test that @app.command without parentheses is not matched."""
        file_content = """
@app.command
def should_not_match():
    pass

@app.command()
def should_match():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["should_match"]

    def test_complex_decorator_expressions(self):
        """Test complex decorator expressions that should not match."""
        file_content = """
@getattr(app, "command")()
def complex_expression():
    pass

@app.command() if True else app.other()
def conditional_decorator():
    pass

@app.command()
def simple_correct():
    pass
"""
        with patch("builtins.open", mock_open(read_data=file_content)):
            result = get_app_command_functions("test_file.py")
            assert result == ["simple_correct"]
