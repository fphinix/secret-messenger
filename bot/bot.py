
from disnake import ApplicationCommandInteraction, Embed
from disnake.ext.commands import InteractionBot

from datetime import datetime
import pytz

from database import Database


bot = InteractionBot(sync_commands=True, test_guilds=[988079158477332481, 882925411858804777])

SPREADSHEET_KEY = "1iBlW-C4odqIE_59uZzoS8B78w_Bk0Eqy9X-AX8jEST4"
timezone = pytz.timezone("Asia/Manila")

database = Database(SPREADSHEET_KEY);

@bot.event
async def on_ready():
    print("Bot is now ready!")

@bot.slash_command(name="confess", description="Confess with a nickname.")
async def confess(inter: ApplicationCommandInteraction, message: str, nickname: str, password: str) -> None:

    await inter.response.defer(ephemeral=True)

    if not await database.is_password_and_nickname_valid(nickname, password, str(inter.author.id)):
        embed = Embed(title="Confession",
                      description="Sorry your nickname and password does not match in the database",
                      timestamp=datetime.now(timezone))
        await inter.edit_original_response(embed=embed)
        return
    
    current_count = await database.increment_counter()
    # description = f"**[{current_count:04}] {nickname} confessed:** {message}"
    description = f"**{nickname} confessed:** {message}\n({current_count:04})"

    embed = Embed(description=description)

    await inter.channel.send(embed=embed)
    return

@bot.slash_command(name="register", description="Register a nickname with a password")
async def register(inter: ApplicationCommandInteraction, nickname: str, password: str) -> None:

    await inter.response.defer(ephemeral=True)
    if await database.is_nickname_duplicate(nickname):
        embed = Embed(title="Confession",
                      description=f"Sorry, the nickname: `{nickname}`, already exists in the database.",
                      timestamp=datetime.now(timezone))
        await inter.edit_original_response(embed=embed)
        return 

    await database.register_nickname(nickname, password, str(inter.author.id))
    embed = Embed(title="Confession",
                  description=f"Successfully registered the nickname: `{nickname}` with password: `{password}`",
                  timestamp=datetime.now(timezone))

    await inter.edit_original_response(embed=embed)
    return 

@bot.slash_command(name="unregister", description="Unregister a nickname with a password")
async def unregister(inter: ApplicationCommandInteraction, nickname: str, password: str) -> None:
    
        await inter.response.defer(ephemeral=True)
        if not await database.is_password_and_nickname_valid(nickname, password, str(inter.author.id)):
            embed = Embed(title="Confession",
                        description=f"Sorry, the nickname: `{nickname}`, does not exist in the database.",
                        timestamp=datetime.now(timezone))
            await inter.edit_original_response(embed=embed)
            return 
    
        await database.unregister_nickname(nickname, password, str(inter.author.id))
        embed = Embed(title="Confession",
                    description=f"RIP 🥀 {nickname}\n\nFly high butterfly 🥹\n\n🕊️ Died peacefully in {datetime.now(timezone).strftime('%b %d, %Y')}")
    
        await inter.channel.send(embed=embed)
        return
    
@bot.slash_command(name="changepassword", description="Change password for a nickname")
async def change_password(inter: ApplicationCommandInteraction, nickname: str, old_password: str, new_password: str) -> None:

    await inter.response.defer(ephemeral=True)
    if not await database.is_password_and_nickname_valid(nickname, old_password, str(inter.author.id)):
        embed = Embed(title="Confession",
                    description=f"Sorry, the nickname: `{nickname}`, does not exist in the database.",
                timestamp=datetime.now(timezone))
        await inter.edit_original_response(embed=embed)
        return 

    await database.change_password(nickname, old_password, new_password, str(inter.author.id))
    embed = Embed(title="Confession",
                description=f"Successfully changed password for the nickname: `{nickname}` from: `{old_password}` to: `{new_password}`",
                timestamp=datetime.now(timezone))

    await inter.edit_original_response(embed=embed)
    return
