
from dotenv import load_dotenv
import os
from bot import bot

load_dotenv()

bot.run(os.environ.get("DISCORD_AUTH_KEY"))


