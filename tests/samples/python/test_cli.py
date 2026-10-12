from click.testing import CliRunner
from typer.testing import CliRunner as TyperRunner

import click_sample
import typer_sample


def test_click_hello():
    result = CliRunner().invoke(click_sample.hello, ["--name", "Ada", "--count", "2"])
    assert result.exit_code == 0 and result.output == "Hello, Ada!\nHello, Ada!\n"
    assert CliRunner().invoke(click_sample.hello, ["--count", "x"]).exit_code == 2


def test_typer_hello():
    result = TyperRunner().invoke(typer_sample.app, ["--name", "Ada", "--count", "2"])
    assert result.exit_code == 0 and result.output == "Hello, Ada!\nHello, Ada!\n"
