import os
from asyncio import sleep
from random import choice

import disnake
from disnake.ext import commands
from dotenv import load_dotenv

# сетуп
load_dotenv(override=True)
TOKEN = os.getenv("DISCORD_TOKEN")
intents = disnake.Intents.all()
name = choice(
    [
        "/boop",
        "/canvas",
        "/countries-eng",
        "/countries-ru",
        "/emoji-world",
        "/lightbulbs",
        "/martian-chess",
        "/minesweeper",
        "/minesweeper-universe",
        "/royal-game-of-ur",
        "/safe",
        "/self-destruction",
        "/switch",
        "/tic-tac-toe",
        "/бу",
        "/turing",
        "/ecosystem (вау!)",
        "/langton",
        "spyware",
        "случайный выбор статуса",
        "GoodbyeDPI",
        "ゆめ2っき",
        "/4d-tic-tac-toe",
    ]
)
bot = commands.Bot(
    command_prefix="/",
    help_command=None,
    intents=intents,
    activity=disnake.Game(name=name),
)

# константы
EMOJI_EXCEPTIONS = [
    "<:discord:1238058501507514430>",
    "http",
    "@everyone",
    "@here",
]


def load():
    for filename in os.listdir("cogwheels"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogwheels.{filename[:-3]}")


async def emoji_server_check(message: disnake.Message, user_message):
    """Удаляет сообщения, содержащие текст, на сервере по эмодзи"""
    if message.guild is None:
        return
    if message.guild.id == 1229508321418154055:
        for e in EMOJI_EXCEPTIONS:
            if e in user_message:
                return
        for char in user_message:
            if char.isalnum() and not char.isnumeric():
                await message.delete()
                await message.author.send(":abc::x:")
                break


# запуск
@bot.event
async def on_ready():
    print(f"{bot.user} запустился!")


@bot.event
async def on_message(message: disnake.Message):
    if message.author == bot.user:
        return
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)
    if message.guild:
        print(f"[{message.guild}] <{channel}> {username}: {user_message}")
    else:
        print(f"<DM> {username}: {user_message}")
    await emoji_server_check(message, user_message)


@bot.slash_command(name="бу", description="пугает буу")
async def boo(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message("boo страшно", ephemeral=True, tts=True)


load()
bot.run(token=TOKEN)
