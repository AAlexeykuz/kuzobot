from random import sample
from time import sleep

import disnake
from disnake.ext import commands

from constants import GUILD_IDS

BOMB = ":boom:"
NUMBERS = [
    ":zero:",
    ":one:",
    ":two:",
    ":three:",
    ":four:",
    ":five:",
    ":six:",
    ":seven:",
    ":eight:",
]

DIFFICULTY_RATIOS = {
    "easy": 0.101,
    "normal": 0.15625,
    "hard": 0.20625,
    "extreme": 0.24,
}

invisible = "ㅤ"


def calculate_bombs(bombs, size):
    return round(size * DIFFICULTY_RATIOS.get(bombs, 0))


def generate_field(side_x, side_y, bombs):
    bombs = (
        calculate_bombs(bombs, side_x * side_y)
        if isinstance(bombs, str)
        else bombs
    )
    bomb_coords = set(sample(range(side_x * side_y), bombs))

    field = [
        "||"
        + (
            BOMB
            if index in bomb_coords
            else NUMBERS[
                sum(
                    (nx + ny * side_x) in bomb_coords
                    for nx in range(max(0, x - 1), min(side_x, x + 2))
                    for ny in range(max(0, y - 1), min(side_y, y + 2))
                    if nx != x or ny != y
                )
            ]
        )
        + "||"
        for y in range(side_y)
        for x in range(side_x)
        for index in [y * side_x + x]
    ]

    return [
        "".join(field[i * side_x : (i + 1) * side_x]) for i in range(side_y)
    ]


class MinesweeperCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="minesweeper", description="игра в сапёр", guild_ids=GUILD_IDS
    )
    async def minesweeper(
        self,
        inter: disnake.ApplicationCommandInteraction,
        size: int = commands.Param(gt=17, lt=56),
        difficulty: str = commands.Param(
            choices={
                "легко": "easy",
                "обычно": "normal",
                "сложно": "hard",
                "душно": "extreme",
            }
        ),
    ):
        # 15 is maximum for phones
        # 56 is maximum for 1920x1080
        field = generate_field(size, size, difficulty)
        if size**2 < 100:
            await inter.response.send_message("\n".join(field))
        else:
            await inter.send(
                f"Всего мин: {calculate_bombs(difficulty, size**2)}"
            )
            for i in field:
                sleep(0.5)
                await inter.channel.send(i)


def setup(bot):
    bot.add_cog(MinesweeperCog(bot))
