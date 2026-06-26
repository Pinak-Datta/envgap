import os

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.getenv("REDIS_URL")
DEBUG = os.getenv("DEBUG", "false")

