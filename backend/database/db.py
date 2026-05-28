from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:12345@localhost:5432/life_sciences_db"

engine = create_engine(DATABASE_URL)

connection = engine.connect()

print("Database Connected Successfully")