"""Reseed the database with Sarah's sample data: python -m app.seed --reset"""
import sys

from . import db

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    db.seed(reset=reset)
    print(f"Seeded database at {db.DB_PATH}" + (" (reset)" if reset else ""))
