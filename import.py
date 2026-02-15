import os
import csv
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)

with open("books.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)  # uses header row automatically

    with engine.begin() as conn:  # auto-commits
        for row in reader:
            isbn = row["isbn"].strip()      # keep as TEXT
            title = row["title"].strip()
            author = row["author"].strip()
            year = int(row["year"])

            conn.execute(
                text("""
                    INSERT INTO books (isbn, title, author, year)
                    VALUES (:isbn, :title, :author, :year)
                """),
                {"isbn": isbn, "title": title, "author": author, "year": year}
            )

print("Books imported successfully.")
