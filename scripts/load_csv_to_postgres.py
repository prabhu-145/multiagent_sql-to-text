import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "raw"

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Please create .env file in project root.")

engine = create_engine(DATABASE_URL)

def clean_table_name(filename: str) -> str:
    return Path(filename).stem.lower().replace("-", "_").replace(" ", "_")

def main():
    csv_files = list(DATA_DIR.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {DATA_DIR}")
        return

    for csv_file in csv_files:
        table_name = clean_table_name(csv_file.name)
        print(f"Loading {csv_file.name} -> {table_name}")

        df = pd.read_csv(csv_file, sep=None, engine="python")
        df.to_sql(table_name, engine, if_exists="replace", index=False)

    print("Done loading CSV files into PostgreSQL.")

if __name__ == "__main__":
    main()