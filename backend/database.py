from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = "mysql+pymysql://root:Amulya%402007@localhost:3306/claude"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # auto-reconnect if connection drops
    pool_recycle=3600,        # recycle connections every hour
    echo=False,               # set True to see all SQL in terminal
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("MySQL connected successfully")
    except Exception as e:
        print(f"MySQL connection failed: {e}")