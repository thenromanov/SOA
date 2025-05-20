import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/postservice")

engine = None
SessionLocal = None


def init_db(max_retries=5, retry_delay=2):
    global engine, SessionLocal
    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting DB {attempt+1}")
            engine = create_engine(DATABASE_URL)
            engine.connect()
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("DB connected")
            return
        except Exception as e:
            logger.warning(f"DB error {attempt+1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retry {retry_delay} sec")
                time.sleep(retry_delay)
            else:
                logger.error("DB failed")
                raise


def get_db():
    global SessionLocal
    if not SessionLocal:
        init_db()
    return SessionLocal()
