from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/loan_db"

engine = create_engine(DATABASE_URL)
