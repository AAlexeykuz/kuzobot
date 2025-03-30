from time import sleep

import disnake
from disnake.ext import commands

ID = "langton_"
BD = "<:black_ant_down:1275024647401766952>"
BL = "<:black_ant_left:1275024657745055807>"
BR = "<:black_ant_right:1275024668427948033>"
BU = "<:black_ant_up:1275024680364937390>"
WD = "<:white_ant_down:1275024694671839326>"
WL = "<:white_ant_left:1275024708185882675>"
WR = "<:white_ant_right:1275024721838084096>"
WU = "<:white_ant_up:1275024736950161472>"
B = "⬛"
W = "⬜"

game = None
game_id = None

WHITE = False
BLACK = True


class Langton:
    def __init__(self, field_size: int):
        self.step_counter: int = 0
        self.step_rate: int = 1
        self.field_size: int = field_size
        self.field: list[list[bool]] = [
            [False for _ in range(field_size)] for _ in range(field_size)
        ]
        self.ant_x, self.ant_y = field_size // 2, field_size // 2
        self.camera_x, self.camera_y = self.ant_x, self.ant_y
        self.direction: int = 0  # 0 - налево, 1 - наверх, 2 - направо, 3 - вниз

    def get_embed(self) -> disnake.Embed:
        self.correct_camera_pos()
        white_directions = [WL, WU, WR, WD]
        black_directions = [BL, BU, BR, BD]
        description = ""
        for y in range(self.camera_y - 6, self.camera_y + 7):
            for x in range(self.camera_x - 6, self.camera_x + 7):
                x = x % self.field_size
                y = y % self.field_size
                color = self.field[y][x]
                if color == WHITE:
                    if x == self.ant_x and y == self.ant_y:
                        description += white_directions[self.direction]
                    else:
                        description += W
                elif x == self.ant_x and y == self.ant_y:
                    description += black_directions[self.direction]
                else:
                    description += B
            description += "\n"
        return disnake.Embed(
            title=f"Муравей Лэнгтона ({self.step_counter})",
            description=description,
        )

    def set_step_rate(self, step_rate: float) -> None:
        self.step_rate = round(step_rate)

    def correct_camera_pos(self) -> None:
        if (
            abs(self.camera_x - self.ant_x) >= 6
            or abs(self.camera_y - self.ant_y) >= 6
        ):
            self.camera_x, self.camera_y = self.ant_x, self.ant_y

    def step(self):
        for _ in range(self.step_rate):
            self.step_counter += 1
            if self.field[self.ant_y][self.ant_x] == WHITE:
                multiplier = 1
                self.field[self.ant_y][self.ant_x] = BLACK
            else:
                multiplier = -1
                self.field[self.ant_y][self.ant_x] = WHITE
            if self.direction == 0:
                self.ant_y = (self.ant_y - multiplier) % self.field_size
            elif self.direction == 1:
                self.ant_x = (self.ant_x + multiplier) % self.field_size
            elif self.direction == 2:
                self.ant_y = (self.ant_y + multiplier) % self.field_size
            else:
                self.ant_x = (self.ant_x - multiplier) % self.field_size
            self.direction = (self.direction + multiplier) % 4


class LangtonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="langton", description="осторожно, гипнотический муравей!"
    )
    async def langton(
        self,
        inter: disnake.ApplicationCommandInteraction,
        steps_per_second: float = 2,
        restart: bool = False,
    ):
        if steps_per_second < 0.1:
            await inter.response.send_message(
                "Слишком маленький шаг", ephemeral=True
            )
            return
        if steps_per_second > 1000:
            await inter.response.send_message(
                "Слишком большой шаг", ephemeral=True
            )
            return
        global game, game_id
        if game is None or restart:
            print("Запущен муравей Лэнгтона")
            game = Langton(150)
        if inter.id != game_id:
            game_id = inter.id
        time_rate = 2
        if steps_per_second > time_rate:
            game.set_step_rate(steps_per_second / time_rate)
        else:
            game.set_step_rate(1)
        await inter.response.send_message("Загрузка...", delete_after=0)
        message = await inter.channel.send(embed=game.get_embed())
        while inter.id == game_id:
            game.step()
            if steps_per_second <= time_rate:
                sleep(1 / steps_per_second)
            else:
                sleep(1 / time_rate)
            await message.edit(embed=game.get_embed())
        await message.delete()


def setup(bot):
    bot.add_cog(LangtonCog(bot))
