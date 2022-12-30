
from disnake import ApplicationCommandInteraction, Embed, Attachment, ForumChannel
from disnake.ext.commands import InteractionBot, Param
from disnake.abc import GuildChannel

from datetime import datetime
import pytz

from database import Database


bot = InteractionBot(sync_commands=True, test_guilds=[988079158477332481, 882925411858804777])

SPREADSHEET_KEY = "1iBlW-C4odqIE_59uZzoS8B78w_Bk0Eqy9X-AX8jEST4"
timezone = pytz.timezone("Asia/Manila")

database = Database(SPREADSHEET_KEY)

@bot.event
async def on_ready():
    print("Bot is now ready!")

@bot.slash_command(name="confess", description="Confess with a nickname")
async def confess(
        inter: ApplicationCommandInteraction,
        message: str,
        attachment: Attachment = Param(default=None, description=f"Image/GIF to attach to the confession"),
        channel: GuildChannel = Param(default=None, description=f"The channel to send the confession to"),
    ) -> None:
    
    await inter.response.defer(ephemeral=True)
    nickname = await database.get_nickname_from_session(str(inter.author.id))
    if nickname is None:
        embed = Embed(title="Error", description="It seems like you haven't logged in yet.\n\nIf you don't have a nickname yet, please register one using `/register`.\n\nIf you have one already, please login via `/login`.\n\nNote that you can create as many nicknames as you like!", color=0xFF0000)
        await inter.edit_original_message(embed=embed)
        return

    if channel is None:
        channel = inter.channel
    
    if channel.permissions_for(inter.guild.me).send_messages is False:
        embed = Embed(title="Error", description="I don't have permission to send messages in that channel!", color=0xFF0000)
        await inter.edit_original_message(embed=embed)
        return

    current_count = await database.increment_counter()
    description = f"**{nickname} confessed:** {message}"

    embed = Embed(description=description)
    if attachment is not None:
        embed.set_image(url=attachment.url)
    embed.set_footer(text=f"Confession ID: {current_count:04}")

    await channel.send(embed=embed)
    await inter.edit_original_message(embed=Embed(title="Success", description="Your confession has been sent!", color=0x00FF00))
    return

@bot.slash_command(name="register", description="Register a new nickname")
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

    await login(inter, nickname, password)
    return

@bot.slash_command(name="login", description="Login to your account")
async def login(inter: ApplicationCommandInteraction, nickname: str, password: str) -> None:
    
    await inter.response.defer(ephemeral=True)
    if not await database.is_password_and_nickname_valid(nickname, password, str(inter.author.id)):
        embed = Embed(title="Confession",
                    description="Sorry your nickname and password does not match in the database",
                    timestamp=datetime.now(timezone))
        await inter.edit_original_response(embed=embed)
        return

    await database.logout_user(str(inter.author.id))

    embed = Embed(title="Confession",
                description=f"Successfully logged in as `{nickname}`",
                timestamp=datetime.now(timezone))

    await database.login_user(nickname, password, str(inter.author.id))

    await inter.edit_original_response(embed=embed)
    return

@bot.slash_command(name="logout", description="Logout from current account")
async def logout(inter: ApplicationCommandInteraction) -> None:
        
        await inter.response.defer(ephemeral=True)
        valid = await database.logout_user(str(inter.author.id))
        if valid is False:
            embed = Embed(title="Error", description="You are not logged in.", color=0xFF0000)
            await inter.edit_original_message(embed=embed)
            return
        
        embed = Embed(title="Confession",
                    description="Successfully logged out",
                    timestamp=datetime.now(timezone))
    
        await inter.edit_original_response(embed=embed)
        return


@bot.slash_command()
async def user(inter: ApplicationCommandInteraction):
    pass

@user.sub_command(name="delete", description="Delete current nickname")
async def delete(inter: ApplicationCommandInteraction, password: str) -> None:

    await inter.response.defer(ephemeral=True)
    nickname = await database.get_nickname_from_session(str(inter.author.id))
    if nickname is None:
        embed = Embed(title="Error", description="You don't have a nickname yet. Please register one using `/register` or if you have one already, login via '/login'.", color=0xFF0000)
        await inter.edit_original_message(embed=embed)
        return
    
    if not await database.is_password_and_nickname_valid(nickname, password, str(inter.author.id)):
        embed = Embed(title="Confession",
                    description=f"Sorry, the nickname: `{nickname}`, does not exist in the database.",
                    timestamp=datetime.now(timezone))
        await inter.edit_original_response(embed=embed)
        return 

    await database.delete_nickname(nickname, password, str(inter.author.id))
    embed = Embed(title="Confession",
                description=f"RIP 🥀 {nickname}\n\nFly high butterfly 🥹\n\n🕊️ Died peacefully in {datetime.now(timezone).strftime('%b %d, %Y')}")

    await inter.channel.send(embed=embed)
    return

@user.sub_command_group()
async def change(inter: ApplicationCommandInteraction):
    pass

@change.sub_command(name="nickname", description="Change current nickname")
async def change_nickname(inter: ApplicationCommandInteraction, nickname: str) -> None:

    await inter.response.defer(ephemeral=True)
    nickname = await database.get_nickname_from_session(str(inter.author.id))
    if nickname is None:
        embed = Embed(title="Error", description="You don't have a nickname yet. Please register one using `/register` or if you have one already, login via '/login'.", color=0xFF0000)
        await inter.edit_original_message(embed=embed)
        return

    await database.change_nickname(nickname, inter.author.id)
    embed = Embed(title="Confession",
                description=f"Successfully changed nickname to `{nickname}`",
                timestamp=datetime.now(timezone))

    await inter.edit_original_response(embed=embed)
    return

@change.sub_command(name="password", description="Change current password")
async def change_password(inter: ApplicationCommandInteraction, old_password: str, new_password: str) -> None:

    await inter.response.defer(ephemeral=True)
    nickname = await database.get_nickname_from_session(str(inter.author.id))
    if nickname is None:
        embed = Embed(title="Error", description="You don't have a nickname yet. Please register one using `/register` or if you have one already, login via `/login`.", color=0xFF0000)
        await inter.edit_original_message(embed=embed)
        return
    
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

@bot.slash_command(name="post", description="Post anonymously on forums")
async def post(
        inter: ApplicationCommandInteraction,
        title: str = Param(description=f"Title of the post"),
        message: str = Param(description=f"Message to post"),
        channel: ForumChannel = Param(description=f"The forum to send the confession to"),
    ) -> None:

    await inter.response.defer(ephemeral=True)
    await channel.create_thread(name=title, content=message, applied_tags={channel.available_tags[0]})
    await inter.edit_original_response(content="Successfully posted anonymously to the forums")
    return

@bot.slash_command(name="prompt", description="Create a prompted confession.")
async def prompt(inter: ApplicationCommandInteraction, ask_a_question: str) -> None:

    await inter.response.defer(ephemeral=True)

    current_count = await database.increment_prompted_question_counter()
    # description = f"**[{current_count:04}] {nickname} confessed:** {message}"
    description = f"{ask_a_question}"
    title = f"Prompted Confession \#{current_count:04}"
      
    embed = Embed(title=title, description=description)

    await inter.channel.send(embed=embed)
    return

@bot.slash_command(name="reply", description="Reply to a prompted confession.")
async def reply(inter: ApplicationCommandInteraction, reply: str, confession_id: str, with_nickname: bool = False) -> None:

    await inter.response.defer(ephemeral=True)
    
    nickname = await database.get_nickname_from_session(str(inter.author.id))
    if nickname is None:
        embed = Embed(title="Error", description="It seems like you haven't logged in yet.\n\nIf you don't have a nickname yet, please register one using `/register`.\n\nIf you have one already, please login via `/login`.\n\nNote that you can create as many nicknames as you like!", color=0xFF0000)
        await inter.edit_original_message(embed=embed)
        return
    
    description = f"** Reply to \#{confession_id:04} ** \n {reply}"
    
    if with_nickname:
        description = f"** {nickname} replied in \#{confession_id:04} ** \n {reply}"
    
    embed = Embed(description=description)
    
    current_count = await database.increment_counter()
    embed.set_footer(text=f"Confession ID: {current_count:04}")
    
    await inter.channel.send(embed=embed)
    return