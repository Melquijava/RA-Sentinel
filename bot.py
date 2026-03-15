import os
from dotenv import load_dotenv

from core.bot import RASentinel


def main():
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN não definido no .env")

    bot = RASentinel()
    bot.run(token)


if __name__ == "__main__":
    main()