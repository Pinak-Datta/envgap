import os


def create_app():
    database_url = os.environ["DATABASE_URL"]
    openai_api_key = os.environ["OPENAI_API_KEY"]
    redis_url = os.getenv("REDIS_URL")
    debug = os.getenv("DEBUG", "false")

    return {
        "database_url": database_url,
        "openai_api_key": openai_api_key,
        "redis_url": redis_url,
        "debug": debug,
    }

