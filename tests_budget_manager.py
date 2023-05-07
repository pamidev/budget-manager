import os
from tempfile import NamedTemporaryFile

import pytest
from click.testing import CliRunner

from budget_manager import cli, Expense, load_or_create_db, find_free_id, compute_total, clear_database


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_add_valid_expense(runner):
    result = runner.invoke(cli, ["add", "10.0", "Valid expense"])
    assert result.exit_code == 0
    assert "Added to database" in result.output


def test_add_invalid_expense(runner):
    result = runner.invoke(cli, ["add", "0", "Invalid expense"])
    assert result.exit_code == 1
    assert "Amount cannot be zero or negative" in result.output


def test_report_empty_database(runner):
    clear_database()
    result = runner.invoke(cli, ["report"])
    assert result.exit_code == 0
    assert "Error: Empty database." in result.output


def test_report_non_empty_database(runner):
    clear_database()
    runner.invoke(cli, ["add", "25.0", "Lunch"])
    runner.invoke(cli, ["add", "50.0", "Gasoline"])
    result = runner.invoke(cli, ["report"])
    assert result.exit_code == 0
    assert "Lunch" in result.output
    assert "Gasoline" in result.output


def test_export_python_empty_database(runner):
    clear_database()
    result = runner.invoke(cli, ["export-python"])
    assert result.exit_code == 0
    assert "[]" in result.output


def test_export_python_non_empty_database(runner):
    clear_database()
    runner.invoke(cli, ["add", "25.0", "Lunch"])
    runner.invoke(cli, ["add", "50.0", "Gasoline"])
    result = runner.invoke(cli, ["export-python"])
    assert result.exit_code == 0
    assert "Lunch" in result.output
    assert "Gasoline" in result.output


def test_import_csv_invalid_path(runner):
    result = runner.invoke(cli, ["import-csv", "invalid/file/path"])
    assert result.exit_code == 1
    assert "Error: Bad file path." in result.output


def test_import_csv_valid_path(runner):
    with NamedTemporaryFile(mode="w", delete=False) as f:
        csv_file_path = f.name
        f.write("amount,description\n25.0,Lunch\n50.0,Gasoline\n")
    result = runner.invoke(cli, ["import-csv", csv_file_path])
    assert result.exit_code == 0
    assert "Imported CSV file" in result.output
    os.unlink(csv_file_path)


def test_find_free_id():
    expenses = [Expense(id=1, amount=25.0, desc="Lunch")]
    assert find_free_id(expenses) == 2
    expenses.append(Expense(id=3, amount=50.0, desc="Gasoline"))
    assert find_free_id(expenses) == 2


def test_load_or_create_db():
    expenses = load_or_create_db()
    assert isinstance(expenses, list)


def test_compute_total():
    expenses = [
        Expense(id=1, amount=10.0, desc="Test Expense 1"),
        Expense(id=2, amount=20.0, desc="Test Expense 2"),
    ]
    assert compute_total(expenses) == 30.0

    expenses = [
        Expense(id=1, amount=100.0, desc="Test Expense 3"),
        Expense(id=2, amount=200.0, desc="Test Expense 4"),
        Expense(id=3, amount=300.0, desc="Test Expense 5"),
    ]
    assert compute_total(expenses) == 600.0

    expenses = []
    assert compute_total(expenses) == 0.0
