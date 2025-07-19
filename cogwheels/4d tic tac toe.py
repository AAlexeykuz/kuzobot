import asyncio
import io
import logging
import re
from itertools import product
from random import shuffle
from typing import Optional

import disnake
import numpy as np
from disnake.ext import commands
from PIL import Image

from constants import GUILD_IDS

game_channels: dict[int, "TicTacToe4D"] = {}


logger = logging.getLogger(__name__)


def extract_timeout_time(content: str) -> int:
    content = content.lower()
    start_phrase = "время на ход: "
    start = content.index(start_phrase)
    return int(content[start + len(start_phrase) : -2])


class TicTacToe4D:
    def __init__(
        self,
        game_message: disnake.Message,
        player_1: disnake.User | disnake.Member,
        player_2: disnake.User | disnake.Member,
        timeout_time: int,
    ) -> None:
        self._game_message: disnake.Message = game_message
        players = [player_1, player_2]
        shuffle(players)
        self._player_x: disnake.User | disnake.Member = players[0]
        self._player_o: disnake.User | disnake.Member = players[1]
        self._current_player: disnake.User | disnake.Member = self._player_x
        self._game_over: str | None = None
        self._last_move: str | None = None
        self._last_move_timestamp: float = 0
        self._timeout_time: int = timeout_time  # секунд

        self._length: int = 4
        self._field: list[list[list[list[None | str]]]] = [
            [
                [[None for _ in range(self._length)] for _ in range(self._length)]
                for _ in range(self._length)
            ]
            for _ in range(self._length)
        ]

    def create_image_file(self) -> disnake.File:
        image = Image.open("images/4d tic tac toe/field.png").convert("RGBA")

        cell_length = 64  # пикселя
        field_length = self._length**2 * cell_length
        paths = {"x": "images/4d tic tac toe/x.png", "o": "images/4d tic tac toe/o.png"}
        winner_paths = {
            "x": "images/4d tic tac toe/winner_x.png",
            "o": "images/4d tic tac toe/winner_o.png",
        }
        winner_row = self._get_winner_row()
        image_x_offset = 2  # пискели
        image_y_offset = 3  # пискли

        for x, y, z, w in product(range(self._length), repeat=4):
            cell = self._get_cell_if_exists(x, y, z, w)
            if cell is None:
                continue

            if winner_row is not None and (x, y, z, w) in winner_row:
                path = winner_paths[cell]
            else:
                path = paths[cell]

            image_to_paste = (
                Image.open(path).convert("RGBA").resize((cell_length, cell_length))
            )

            # магический код не трогать
            image_x: int = (
                cell_length * x + self._length * cell_length * z + image_x_offset
            )
            image_y: int = (
                field_length
                + image_y_offset
                - (cell_length * (y + 1) + self._length * cell_length * w)
            )

            image.paste(image_to_paste, (image_x, image_y), mask=image_to_paste)

        image_binary = io.BytesIO()
        image.save(image_binary, format="PNG")
        image_binary.seek(0)
        return disnake.File(image_binary, filename="field.png")

    def _get_winner_row(self) -> Optional[list[tuple[int, int, int, int]]]:
        """Возвращает множество всех координат, которые принадлежат выигрышному ряду"""
        for x, y, z, w in product(range(self._length), repeat=4):
            winner_row = self._get_winner_row_from_point(x, y, z, w)
            if winner_row:
                return winner_row
        return None

    def create_status_message(self) -> str:
        if self._game_over == "timeout":
            return (
                f"У игрока {self._current_player.mention} закончилось время на ход ({self._timeout_time}с). "
                f"Победа {self._get_other_player(self._current_player).mention}!"
            )
        if self._game_over == "draw":
            return "Свободных клеток больше нет! Ничья!"
        if self._game_over == "win":
            return f"Победа {self._current_player.mention}! Игра окончена."
        if self._last_move is None:
            return f"Первым ходит {self._current_player.mention}!"
        return f"Ход {self._current_player.mention}\nПоследний ход: {self._last_move}"

    def _get_cell_if_exists(self, *coords) -> None | str:
        if not all(0 <= coord < self._length for coord in coords):
            return None
        x, y, z, w = coords
        return self._field[x][y][z][w]

    def _get_winner_row_from_point(
        self, x: int, y: int, z: int, w: int
    ) -> Optional[list[tuple[int, int, int, int]]]:
        """Возвращает координаты выигрышного ряда,
        если один из четырёхмерных рядов из этой точки оказался выигрышным"""

        # оптимизация (внутренние клетки не проверяются)
        if all(0 < coord < self._length - 1 for coord in (x, y, z, w)):
            return None

        for direction in product((-1, 0, 1), repeat=4):  # repeat=4 т.к. 4 измерения
            if direction == (0, 0, 0, 0):
                continue
            row_coords = [
                np.array(direction) * i + np.array([x, y, z, w])
                for i in range(self._length)
            ]
            if all(
                self._get_cell_if_exists(*coords) == self._get_current_player_character()
                for coords in row_coords
            ):
                return [tuple(coords.tolist()) for coords in row_coords]
        return None

    def _switch_players(self) -> None:
        if self._current_player == self._player_x:
            self._current_player = self._player_o
        else:
            self._current_player = self._player_x

    def _update_game_over(self) -> None:
        if any(
            self._get_winner_row_from_point(x, y, z, w)
            for x, y, z, w in product(range(self._length), repeat=4)
        ):
            self._game_over = "win"
        if (
            all(
                self._get_cell_if_exists(x, y, z, w) is not None
                for x, y, z, w in product(range(self._length), repeat=4)
            )
            and not self._game_over
        ):
            self._game_over = "draw"

    async def update(self) -> None:
        if not self._game_over:
            self._update_game_over()

        if not self._game_over:
            self._switch_players()
        else:
            del game_channels[self._game_message.channel.id]
        await self._update_game_message()

    async def _update_game_message(self) -> None:
        view = GameView() if not self._game_over else None
        await self._game_message.edit(
            content=self.create_status_message(),
            file=self.create_image_file(),
            view=view,
        )

    def _is_occupied(self, x: int, y: int, z: int, w: int) -> bool:
        return self._field[x][y][z][w] is not None

    def _get_current_player_character(self) -> str:
        return "x" if self._current_player == self._player_x else "o"

    def _make_a_move(self, x: int, y: int, z: int, w: int) -> None:
        player = self._get_current_player_character()
        self._field[x][y][z][w] = player

    def handle_message(self, message: disnake.Message) -> bool:
        if message.author != self._current_player:
            return False

        content = re.sub(r"\s+", "", message.content).lower()

        try:
            letter = content[0]
            first_coord = "abcdefghijklmnop".index(letter)
        except Exception:
            return False

        try:
            second_coord = int(content[1:]) - 1
            if not (0 <= second_coord <= self._length**2 - 1):
                return False
        except Exception:
            return False

        x = first_coord % self._length
        y = second_coord % self._length
        z = first_coord // self._length
        w = second_coord // self._length

        if self._is_occupied(x, y, z, w):
            return False

        self._make_a_move(x, y, z, w)
        self._last_move = content.upper()
        self._last_move_timestamp = message.created_at.timestamp()

        return True

    def get_current_player(self) -> disnake.User | disnake.Member:
        return self._current_player

    def _get_other_player(
        self, player: disnake.User | disnake.Member
    ) -> disnake.User | disnake.Member:
        """Возвращает игрока, отличного от данного"""
        return self._player_x if player == self._player_o else self._player_o

    def get_players(
        self,
    ) -> tuple[disnake.User | disnake.Member, disnake.User | disnake.Member]:
        return self._player_x, self._player_o

    async def timeout(self, last_move_timestamp: float) -> None:
        await asyncio.sleep(self._timeout_time)
        if last_move_timestamp >= self._last_move_timestamp:
            self._game_over = "timeout"
            await self.update()

    async def resign(self, player: disnake.User | disnake.Member) -> None:
        winner = self._get_other_player(player)
        await self._game_message.edit(
            content=f"{player.mention} сдался. Победа {winner.mention}!",
            view=None,
        )
        del game_channels[self._game_message.channel.id]


class AgreeOnGameView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Сыграть", style=disnake.ButtonStyle.green, custom_id="agree_on_game:agree"
    )
    async def agree_button(
        self, _: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        if inter.channel.id in game_channels:
            await inter.response.send_message(
                "В этом канале уже ведётся игра.", ephemeral=True
            )
            return
        if inter.message.interaction is None:
            await inter.response.send_message(
                "Возникла ошибка: видимо, это сообщение каким-то образом было создано без команды.",
                ephemeral=True,
            )
            return
        timeout_time = extract_timeout_time(inter.message.content)
        game = TicTacToe4D(
            inter.message, inter.message.interaction.author, inter.author, timeout_time
        )
        game_channels[inter.channel_id] = game
        await inter.response.edit_message(
            content=game.create_status_message(),
            file=game.create_image_file(),
            view=GameView(),
        )
        await inter.followup.send(
            f"{game.get_current_player().mention}, ваш ход!", delete_after=5
        )
        await game.timeout(inter.created_at.timestamp())


class GameView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Как играть",
        style=disnake.ButtonStyle.blurple,
        custom_id="game_view:info",
    )
    async def info_button(
        self, _: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        message = (
            "Чтобы победить, вам нужно собрать 4 ваших значка в ряд.\n"
            "Ряд - любая диагональ или прямая, включая трёхмерные и четырёхмерные (как на картинке). "
            "Вы используете две координаты, чтобы указать куда ходите, "
            "но в действительности игровое поле - это тессеракт 4x4x4x4."
            "Чтобы походить, напишите сначала букву, затем цифру. Например, H9"
            "Иногда ход может обрабатываться несколько секунд."
        )

        image = Image.open("images/4d tic tac toe/tutorial.png")
        image_binary = io.BytesIO()
        image.save(image_binary, format="PNG")
        image_binary.seek(0)
        file = disnake.File(image_binary, filename="tutorial.png")

        await inter.response.send_message(message, ephemeral=True, file=file)

    @disnake.ui.button(
        label="Сдаться",
        style=disnake.ButtonStyle.red,
        custom_id="game_view:resign",
    )
    async def resign_button(
        self, _: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        if inter.channel_id not in game_channels:
            await inter.response.send_message("Эта игра уже окончена.", ephemeral=True)
            return
        game = game_channels[inter.channel_id]
        if inter.author not in game.get_players():
            await inter.response.send_message("Это не ваша игра.", ephemeral=True)
            return
        await game.resign(inter.author)


class TicTacToe4DCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.setup())

    async def setup(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(AgreeOnGameView())
        self.bot.add_view(GameView())

    @commands.slash_command(
        name="4d-tic-tac-toe", description="4д крестики нолики", guild_ids=GUILD_IDS
    )
    @commands.guild_only()
    async def command(
        self,
        inter: disnake.ApplicationCommandInteraction,
        timeout_time: int = 300,
    ) -> None:
        if inter.channel.id in game_channels:
            await inter.response.send_message(
                "В этом канале уже ведётся игра.", ephemeral=True
            )
            return
        message = f"{inter.author.mention} предлагает сыграть в 4D крестики-нолики. \nВремя на ход: {timeout_time}с."
        await inter.response.send_message(message, view=AgreeOnGameView())

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.channel.id not in game_channels:
            return
        game = game_channels[message.channel.id]
        if game.handle_message(message):
            await message.delete()
            asyncio.create_task(game.timeout(message.created_at.timestamp()))
            await game.update()


def setup(bot: commands.Bot):
    bot.add_cog(TicTacToe4DCog(bot))
