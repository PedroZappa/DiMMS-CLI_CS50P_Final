import pytest
from typer.testing import CliRunner
from project import app

runner = CliRunner()

def test_app():
    result = runner.invoke(app, ["search-artists", "Muse"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["list-albums", "1"])
    assert result.exit_code == 0

    result = runner.invoke(app, [""])
    assert result.exit_code == 2
