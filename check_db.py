
import sqlite3
import os

db_path = "moltlook.db"

def check_db():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- Table Schemas ---")
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table_name, sql in tables:
        print(f"Table: {table_name}")
        print(sql)
        print("-" * 20)

    print("\n--- Indexes ---")
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index';")
    indexes = cursor.fetchall()
    for index_name, tbl_name, sql in indexes:
        print(f"Index: {index_name} on {tbl_name}")
        print(sql)
        print("-" * 20)

    print("\n--- Row Counts ---")
    for table_name, _ in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name}: {count}")

    conn.close()

if __name__ == "__main__":
    check_db()
