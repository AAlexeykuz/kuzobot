import asyncio
from random import shuffle

import disnake
from disnake import ui
from disnake.ext import commands

ID = "boop_"
BG = "<:h:1274084516134256732>"
WK = "<:h:1274297399342534698>"
WC = "<:h:1274295813157158993>"
BK = "<:h:1274295788826136620>"
BC = "<:h:1274297619572592640>"
BGA = "<:h:1274791565688180741>"
WKA = "<:h:1274302755355492363>"
WCA = "<:h:1274302766273003560>"
BKA = "<:h:1274302731678515260>"
BCA = "<:h:1274302742499819562>"
BCW = "<:h:1274842070657532098>"
WCW = "<:h:1274845179894956124>"

WHITE = 0
BLACK = 1
ARROWS = {
    (-1, -1): "↖️",
    (-1, 0): "⬅️",
    (-1, 1): "↙️",
    (0, -1): "⬆️",
    (0, 1): "⬇️",
    (1, -1): "↗️",
    (1, 0): "➡️",
    (1, 1): "↘️",
}

active_games: dict[int:"Boop"] = dict()


class Piece:
    def __init__(self, color: int, adult: bool):
        self.color = color
        self.adult = adult
        if color == WHITE:
            if adult:
                self.emoji, self.appearance = WC, WCA
            else:
                self.emoji, self.appearance = WK, WKA
        elif adult:
            self.emoji, self.appearance = BC, BCA
        else:
            self.emoji, self.appearance = BK, BKA

    def get_emoji(self, appearance=False):
        if appearance:
            return self.appearance
        return self.emoji

    def get_color(self) -> int:
        return self.color

    def is_adult(self) -> bool:
        return self.adult


def text_to_coords(s: str):
    if len(s) != 2:
        return None
    letters = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5}
    col, row = s[0], s[1]
    if row not in "123456" or col not in "abcdef":
        return None
    return 6 - int(row), letters[col]


def coords_to_text(coords: tuple) -> str:
    letters = ["a", "b", "c", "d", "e", "f"]
    return f"{letters[coords[1]]}{6 - coords[0]}"


class Boop:
    def __init__(self, inter: disnake.MessageInteraction):
        self.inter = inter
        self.game_message = None
        players = [inter.author, inter.message.interaction.author]
        shuffle(players)
        self.white: disnake.Member = players[0]
        self.black: disnake.Member = players[1]
        self.turn = WHITE
        self.last_piece = None
        self.last_boops = dict()
        self.last_graduates = list()
        self.is_graduating = False
        self.is_game_over = False
        self.win_row = list()

        self.white_kittens: int = 8
        self.white_cats: int = 0
        self.black_kittens: int = 8
        self.black_cats: int = 0

        self.field: list[list] = [[None for _ in range(6)] for _ in range(6)]

    def set_game_message(self, message: disnake.Message) -> None:
        self.game_message = message

    def get_message(self) -> str:
        numbers = [
            ":zero:",
            ":one:",
            ":two:",
            ":three:",
            ":four:",
            ":five:",
            ":six:",
            ":seven:",
            ":eight:",
            ":nine:",
        ]

        output = f":white_circle:{self.white.mention} VS {self.black.mention}:black_circle:\n"
        output += (
            f"{numbers[self.white_kittens]}{WK}\t\t\t\t   {BK}{numbers[self.black_kittens]}\n"
            f"{numbers[self.white_cats]}{WC}\t\t\t\t   {BC}{numbers[self.black_cats]}\n\n"
        )

        for i in range(len(self.field)):
            output += numbers[6 - i]
            for j in range(len(self.field[i])):
                piece = self.field[i][j]
                if (j, i) in self.last_boops:
                    output += self.last_boops[(j, i)]
                elif (i, j) in self.last_graduates:
                    output += BGA
                elif piece is not None and (i, j) in self.win_row:
                    if piece.get_color() == WHITE:
                        output += WCW
                    else:
                        output += BCW
                elif piece is None:
                    output += BG
                else:
                    output += piece.get_emoji(
                        appearance=piece == self.last_piece
                    )
            output += "\n"
        output += (
            ":black_heart::regional_indicator_a::regional_indicator_b::regional_indicator_c:"
            ":regional_indicator_d::regional_indicator_e::regional_indicator_f:"
        )

        return output

    @staticmethod
    def get_components() -> list:
        return [
            ui.Button(
                label="Правила",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "help",
            ),
            ui.Button(
                label="Сдаться",
                style=disnake.ButtonStyle.danger,
                custom_id=ID + "resign",
            ),
        ]

    def main_loop(self) -> None:
        pass

    def get_players(self) -> tuple[disnake.Member, disnake.Member]:
        return self.white, self.black

    def get_current_player(self) -> disnake.Member:
        if self.turn == WHITE:
            return self.white
        return self.black

    def swap_players(self) -> None:
        if self.turn == WHITE:
            self.turn = BLACK
        else:
            self.turn = WHITE

    def get_cats_and_kittens(self):
        if self.turn == WHITE:
            return self.white_cats, self.white_kittens
        return self.black_cats, self.black_kittens

    def make_move(self, message: str) -> str:
        cats, kittens = self.get_cats_and_kittens()
        self.last_piece = None
        if len(message) != 2:
            return ""
        coords = text_to_coords(message.lower())
        if not coords:
            return ""
        if self.field[coords[0]][coords[1]] is not None:
            return "Некорректный ход"
        if kittens <= 0 and message[0].islower():
            return "Недостаточно котят для этого хода"
        if cats <= 0 and message[0].isupper():
            return "Недостаточно кошек для этого хода"
        self._place_piece(coords, message[0].isupper())
        return "ok"

    @staticmethod
    def check_coords(coords) -> bool:
        y, x = coords
        return 5 >= y >= 0 and 5 >= x >= 0

    def _place_piece(self, coords: tuple[int, int], adult: bool) -> None:
        row, col = coords
        piece = Piece(self.turn, adult)
        self.last_piece = piece
        self.field[row][col] = piece
        self.last_boops = dict()
        if self.turn == WHITE:
            if adult:
                self.white_cats -= 1
            else:
                self.white_kittens -= 1
        elif adult:
            self.black_cats -= 1
        else:
            self.black_kittens -= 1
        for x_offset in (-1, 0, 1):
            for y_offset in (-1, 0, 1):
                if x_offset == 0 and y_offset == 0:
                    continue
                x, y = x_offset + col, y_offset + row
                if not self.check_coords((x, y)):
                    continue
                piece = self.field[y][x]
                if piece is not None and (adult or not piece.is_adult()):
                    x_2, y_2 = x_offset * 2 + col, y_offset * 2 + row
                    if not self.check_coords((x_2, y_2)):
                        self.field[y][x] = None
                        self.last_boops[(x, y)] = ARROWS[(x_offset, y_offset)]
                        if piece.get_color() == WHITE:
                            if piece.is_adult():
                                self.white_cats += 1
                            else:
                                self.white_kittens += 1
                        elif piece.is_adult():
                            self.black_cats += 1
                        else:
                            self.black_kittens += 1
                        continue
                    piece_2 = self.field[y_2][x_2]
                    if piece_2 is None:
                        self.field[y_2][x_2] = piece
                        self.field[y][x] = None
                        self.last_boops[(x, y)] = ARROWS[(x_offset, y_offset)]

    def is_win(self) -> int:
        for row in range(len(self.field)):
            for col in range(len(self.field[row])):
                main_piece = self.field[row][col]
                if (
                    main_piece is None
                    or not main_piece.is_adult()
                    or main_piece.get_color() != self.turn
                ):
                    continue
                for offset in ((1, 1), (-1, 1), (1, 0), (0, 1)):
                    graduation_row = [
                        (row + offset[0], col + offset[1]),
                        (row, col),
                        (row - offset[0], col - offset[1]),
                    ]
                    pass_flag = True
                    for coords in graduation_row:
                        if not self.check_coords(coords):
                            pass_flag = False
                            break
                        piece = self.field[coords[0]][coords[1]]
                        if (
                            piece is None
                            or not piece.is_adult()
                            or piece.get_color() != main_piece.get_color()
                        ):
                            pass_flag = False
                            break
                    if pass_flag:
                        for i in graduation_row:
                            self.win_row.append(i)
                        return 1
        cat_count = 0
        for i in range(len(self.field)):
            for j in range(len(self.field[i])):
                piece = self.field[i][j]
                if (
                    piece is not None
                    and piece.is_adult()
                    and piece.get_color() == self.turn
                ):
                    self.win_row.append((i, j))
                    cat_count += 1
        if cat_count >= 8:
            return 2
        self.win_row = list()
        return 0

    def get_graduation_rows(self) -> list:
        self.last_graduates = []
        graduation_rows = []
        for row in range(len(self.field)):
            for col in range(len(self.field[row])):
                main_piece = self.field[row][col]
                if main_piece is None or main_piece.get_color() != self.turn:
                    continue
                for offset in ((1, 1), (-1, 1), (1, 0), (0, 1)):
                    graduation_row = [
                        (row + offset[0], col + offset[1]),
                        (row, col),
                        (row - offset[0], col - offset[1]),
                    ]
                    pass_flag = True
                    for coords in graduation_row:
                        if not self.check_coords(coords):
                            pass_flag = False
                            break
                        piece = self.field[coords[0]][coords[1]]
                        if (
                            piece is None
                            or piece.get_color() != main_piece.get_color()
                        ):
                            pass_flag = False
                            break
                    if pass_flag:
                        graduation_rows.append(graduation_row)
        return graduation_rows

    def graduate_row(self, row: str) -> None:
        row = row.split("-")
        for i in range(len(row)):
            row[i] = text_to_coords(row[i])
        for coords in row:
            self.graduate_cell(coords)

    def graduate_cell(self, coords: tuple[int, int]) -> None:
        piece = self.field[coords[0]][coords[1]]
        self.field[coords[0]][coords[1]] = None
        self.last_graduates.append(coords)
        if piece.get_color() == WHITE:
            self.white_cats += 1
        else:
            self.black_cats += 1

    @staticmethod
    def get_graduation_row_buttons(rows) -> list[ui.Button]:
        buttons = []
        for row in rows:
            row.sort()
            coords = []
            for coord in row:
                coords.append(coords_to_text(coord))
            label = "-".join(coords)
            buttons.append(
                ui.Button(
                    label=label.upper(),
                    style=disnake.ButtonStyle.primary,
                    custom_id=ID + "graduate_" + label,
                )
            )
        return buttons

    def get_graduation_cells_buttons(self) -> list[ui.Button]:
        buttons = []
        for i in range(len(self.field)):
            for j in range(len(self.field)):
                piece = self.field[i][j]
                if piece is not None and piece.get_color() == self.turn:
                    label = coords_to_text((i, j))
                    buttons.append(
                        ui.Button(
                            label=label.upper(),
                            style=disnake.ButtonStyle.primary,
                            custom_id=ID + "graduate_cell_" + label,
                        )
                    )
        return buttons

    @staticmethod
    def graduation_row_into_text(row: list[tuple[int, int]]) -> str:
        output = []
        for i in row:
            output.append(coords_to_text(i))
        return "-".join(output)

    def game_over(self) -> None:
        global active_games
        if self.inter.channel_id in active_games:
            del active_games[self.inter.channel_id]
        self.is_game_over = True

    def current_has_cats(self) -> bool:
        if self.turn == WHITE:
            return self.white_kittens > 0 or self.white_cats > 0
        return self.black_kittens > 0 or self.black_cats > 0


class BoopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="boop", description="пуньк! игра про котиков")
    async def boop(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            f"Игра в Пуньк с {inter.author.mention}",
            components=[
                ui.Button(
                    label="Присоединиться",
                    style=disnake.ButtonStyle.primary,
                    custom_id=ID + "join",
                )
            ],
        )

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith(ID):
            return
        action = inter.component.custom_id[len(ID) :]
        global active_games

        if action == "join":
            if inter.channel_id in active_games:
                await inter.response.send_message(
                    "Игра уже началась в этом канале", ephemeral=True
                )
                return
            game = Boop(inter)
            active_games[inter.channel_id] = game
            await inter.message.edit(
                game.get_message(), components=game.get_components()
            )
            await inter.response.send_message(
                f"{game.white.mention} играет против {game.black.mention} "
                f"и ходит первым!",
                delete_after=5,
            )
            game_message = inter.message
            game.set_game_message(game_message)
            while inter.channel_id in active_games:
                try:
                    if not game.current_has_cats() and not game.is_graduating:
                        buttons = game.get_graduation_cells_buttons()
                        if buttons:
                            await inter.channel.send(
                                f"У {game.get_current_player().mention} закончились котики! "
                                f"Поэтому вы можете превратить любого котёнка на поле в кошку "
                                f"(или забрать кошку обратно). "
                                f"Выберите клетку.",
                                components=buttons,
                            )
                        else:
                            game.game_over()
                            if game.turn == WHITE:
                                await inter.channel.send(
                                    "Белые победили, поставив 8 кошек на поле! Спасибо за игру."
                                )
                            else:
                                await inter.channel.send(
                                    "Чёрные победили, поставив 8 кошек на поле! Спасибо за игру."
                                )
                            break
                        game.is_graduating = True
                    message = await self.bot.wait_for(
                        "message",
                        check=lambda x: x.channel.id == inter.channel_id
                        and x.author == game.get_current_player(),
                        timeout=500,
                    )
                    if game.is_graduating:
                        continue
                    if game.is_game_over:
                        break
                    result = game.make_move(message.content.strip())
                    if result == "ok":
                        await message.delete()
                        graduation_rows = game.get_graduation_rows()
                        win = game.is_win()
                        if win == 1:
                            if game.turn == WHITE:
                                await inter.channel.send(
                                    "Белые победили! Спасибо за игру."
                                )
                            else:
                                await inter.channel.send(
                                    "Чёрные победили! Спасибо за игру."
                                )
                            game.game_over()
                        elif win == 2:
                            if game.turn == WHITE:
                                await inter.channel.send(
                                    "Белые победили, поставив 8 кошек на поле! Спасибо за игру."
                                )
                            else:
                                await inter.channel.send(
                                    "Чёрные победили, поставив 8 кошек на поле! Спасибо за игру."
                                )
                            game.game_over()
                        elif len(graduation_rows) == 1:
                            game.graduate_row(
                                game.graduation_row_into_text(
                                    graduation_rows[0]
                                )
                            )
                            game.swap_players()
                        elif len(graduation_rows) >= 2:
                            game.is_graduating = True
                            await inter.channel.send(
                                f"{game.get_current_player().mention}, выберите ряд, "
                                f"который хотите превратить в кошек.",
                                components=game.get_graduation_row_buttons(
                                    graduation_rows
                                ),
                            )
                        else:
                            game.swap_players()
                        await game_message.edit(game.get_message())
                    elif not result:
                        continue
                    else:
                        await inter.channel.send(result, delete_after=2.5)
                        await message.delete()
                        continue
                except asyncio.TimeoutError:
                    game.game_over()
                    loser = game.get_current_player()
                    await inter.followup.send(
                        f"{loser.mention} слишком много думал и проиграл."
                    )
                    await game_message.edit(game.get_message())
                if game.is_game_over:
                    return
        if action == "join":
            return
        if action == "help":
            await inter.response.send_message(
                """Правила игры /boop:
- Игроки по очереди ставят фигуры на поле.
```Чтобы поставить котёнка на поле, напишите в чат координаты клетки (сначала буква, потом цифра) Например, b4.
Если вы хотите поставить кошку, то напишите букву большой, например, A3.```
- Когда вы ставите на поле котёнка, он пунькает всех соседних котят на одну клетку, если ему не мешает другая фигура. Котёнок может столкнуть других котят с поля.
- Если вы соберёте три ваших котёнка или кошки в ряд (в любом направлении), то ряд убирается с поля, а все котята, что были в ряду, заменяются на кошек. (Это проверяется после вашего хода)
- Кошки большие, поэтому их могут пунькать только другие кошки. Их тоже можно столкнуть с поля.
- Первый, кто соберёт три кошки в ряд или поставит все 8 кошек на поле, победит. (Это проверяется после вашего хода).
Дополнительные правила:
- Если у вас не осталось котят или кошек, которые вы можете поставить, то вы можете превратить любого вашего котёнка на поле в кошку.
Подробнее: <https://rules.dized.com/game/3_U-I3tNQyW4X0aaWER7YA/boop>""",
                ephemeral=True,
            )
            return
        if inter.channel_id not in active_games:
            await inter.response.send_message(
                "Эта игра уже закончилась. "
                "Откройте новую с помощью команды /boop",
                ephemeral=True,
            )
            return
        game = active_games[inter.channel_id]
        if inter.author not in game.get_players():
            await inter.response.send_message(
                "Это не ваша игра. "
                "Начните новую в другом канале с помощью команды /boop",
                ephemeral=True,
            )
        elif action == "resign":
            await inter.response.send_message(f"{inter.author.mention} сдался.")
            game.game_over()
        elif inter.author != game.get_current_player():
            await inter.response.send_message(
                "Это чужая кнопка, вы не можете на неё нажать.", ephemeral=True
            )
        elif "graduate_cell_" in action:
            game.graduate_cell(text_to_coords(action[14:]))
            game.is_graduating = False
            await inter.message.delete()
            await game.game_message.edit(game.get_message())
        elif "graduate_" in action:
            game.graduate_row(action[9:])
            game.is_graduating = False
            game.swap_players()
            if game.turn == WHITE:
                await inter.message.edit(
                    "Ход белых!", components=[], delete_after=2
                )
            else:
                await inter.message.edit(
                    "Ход чёрных!", components=[], delete_after=2
                )
            await game.game_message.edit(game.get_message())


def setup(bot):
    bot.add_cog(BoopCog(bot))
