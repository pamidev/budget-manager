import csv
import pickle
import sys
from dataclasses import dataclass

import click

DB_FILENAME = r".\data\budget-database.db"
MUCH_EXPENSIVE = 1000


@dataclass
class Expense:
    id: int
    amount: float
    desc: str

    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Amount cannot be zero or negative.")
        if not self.desc:
            raise ValueError("Description cannot be empty.")

    def is_expensive(self) -> bool:
        return self.amount >= MUCH_EXPENSIVE


def find_free_id(expenses: list[Expense]) -> int:
    all_ids = {expense.id for expense in expenses}
    next_id = 1
    while next_id in all_ids:
        next_id += 1
    return next_id


def load_or_create_db() -> list[Expense]:
    try:
        with open(DB_FILENAME, 'rb') as stream:
            expenses = pickle.load(stream)
    except FileNotFoundError:
        expenses = []
    return expenses


def clear_database() -> None:
    with open(DB_FILENAME, "wb") as stream:
        pickle.dump([], stream)


def save_expenses(expenses: list[Expense]) -> None:
    with open(DB_FILENAME, 'wb') as stream:
        pickle.dump(expenses, stream)


def compute_total(expenses: list[Expense]) -> float:
    amounts = [e.amount for e in expenses]
    return sum(amounts)


def read_csv(filepath: str):
    try:
        with open(filepath) as stream:
            reader = csv.DictReader(stream)
            expenses_from_csv = [expense for expense in reader]
    except FileNotFoundError:
        print(":-( Error: Bad file path.")
        sys.exit(1)
    return expenses_from_csv


def print_report(expenses: list[Expense], total: float) -> None:
    if expenses:
        print("---------------------------------------------------------")
        print(f"{'ID':^5} {'AMOUNT (PLN)':^18} {'BIG?':<6} {'DESCRIPTION'}")
        print("---------------------------------------------------------")
        for expense in expenses:
            if expense.is_expensive():
                warning = '(!)'
            else:
                warning = ''
            print(
                f"{expense.id:5d} {expense.amount:15.2f} {warning:^9} {expense.desc}"
            )
        print("---------------------------------------------------------")
        print(f"{'TOTAL:':>6} {total:14.2f}")
        print("---------------------------------------------------------")
    else:
        print(":-( Error: Empty database.")


@click.group()
def cli():
    pass


@cli.command()
@click.argument('amount', type=float)
@click.argument('description', type=str)
def add(amount: float, description: str) -> None:
    expenses = load_or_create_db()
    next_id = find_free_id(expenses)
    try:
        new_expense = Expense(id=next_id, amount=amount, desc=description)
    except ValueError as e:
        print(f":-( Error: {e.args[0]}")
        sys.exit(1)

    expenses.append(new_expense)
    save_expenses(expenses)
    click.echo(":-) Added to database.")


@cli.command()
def report() -> None:
    expenses = load_or_create_db()
    total = compute_total(expenses)
    print_report(expenses, total)


@cli.command('clear-db')
def clear_db():
    decision = input("Are You sure? (Y/N): ")
    if decision.lower() == "y":
        clear_database()


@cli.command('export-python')
def export_python():
    expenses = load_or_create_db()
    print(expenses)


@cli.command('import-csv')
@click.argument('csv_filepath', type=str)
def import_csv(csv_filepath: str) -> None:
    expenses = load_or_create_db()

    try:
        with open(csv_filepath) as stream:
            reader = csv.DictReader(stream)
            for row in reader:
                csv_expense = Expense(
                    id=find_free_id(expenses),
                    amount=float(row['amount']),
                    desc=row['description'],
                )
                expenses.append(csv_expense)
    except FileNotFoundError:
        print(":-( Error: Bad file path.")
        sys.exit(1)

    save_expenses(expenses)
    print(":-) Imported CSV file and added to database.")


if __name__ == "__main__":
    cli()
