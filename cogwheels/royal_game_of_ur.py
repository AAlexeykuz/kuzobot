from random import randint, shuffle

import disnake
from disnake import ui
from disnake.ext import commands

ID = "royal_game_of_ur_"
BLACK = ":black_large_square:"
ORANGE = ":orange_square:"
YELLOW = ":yellow_square:"
ROSETTE = ":red_square:"
BLACK_PIECE = ":brown_circle:"
WHITE_PIECE = ":white_circle:"
ONES_AND_ZEROS = [":small_red_triangle_down:", ":small_red_triangle:"]

active_games = dict()


class Board:
    def __init__(
        self,
        player1: disnake.Member,
        player2: disnake.Member,
        message: disnake.Message,
    ):
        player_list = [player1, player2]
        shuffle(player_list)
        self.white_player, self.black_player = player_list[0], player_list[1]
        self.current_player = self.white_player
        self.other_player = self.black_player
        self.white_pieces = [-1 for _ in range(7)]
        self.black_pieces = [-1 for _ in range(7)]
        self.white_path = [
            (3, 0),
            (2, 0),
            (1, 0),
            (0, 0),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            (6, 1),
            (7, 1),
            (7, 0),
            (6, 0),
        ]
        self.black_path = [
            (3, 2),
            (2, 2),
            (1, 2),
            (0, 2),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            (6, 1),
            (7, 1),
            (7, 2),
            (6, 2),
        ]
        self.counter = [
            ":zero:",
            ":one:",
            ":two:",
            ":three:",
            ":four:",
            ":five:",
            ":six:",
            ":seven:",
        ]
        self.original_message = message
        self.last_roll = None

    def __str__(self):
        field = [
            [ROSETTE, ORANGE, ROSETTE],
            [ORANGE, YELLOW, ORANGE],
            [YELLOW, ORANGE, YELLOW],
            [ORANGE, ROSETTE, ORANGE],
            [
                self.counter[self.white_pieces.count(-1)],
                ORANGE,
                self.counter[self.black_pieces.count(-1)],
            ],
            [
                self.counter[7 - len(self.white_pieces)],
                YELLOW,
                self.counter[7 - len(self.black_pieces)],
            ],
            [ROSETTE, ORANGE, ROSETTE],
            [ORANGE, YELLOW, ORANGE],
        ]
        output = ""
        for i in self.white_pieces:
            if -1 < i < 14:
                x, y = self.white_path[i]
                field[x][y] = WHITE_PIECE
        for i in self.black_pieces:
            if -1 < i < 14:
                x, y = self.black_path[i]
                field[x][y] = BLACK_PIECE
        for i in field:
            output += "".join(i) + "\n"
        return output

    def swap_players(self):
        if self.current_player is self.white_player:
            self.current_player = self.black_player
            self.other_player = self.white_player
        else:
            self.current_player = self.white_player
            self.other_player = self.black_player

    def get_pieces(self):
        if self.is_white():
            return self.white_pieces
        return self.black_pieces

    def get_other_pieces(self):
        if self.is_white():
            return self.black_pieces
        return self.white_pieces

    def get_player(self):
        return self.current_player

    def is_white(self):
        return self.current_player is self.white_player

    def is_game_over(self):
        if len(self.white_pieces) == 0 or len(self.black_pieces) == 0:
            return True
        return False

    def get_other_player(self):
        return self.other_player

    def get_buttons(self, roll_number):
        buttons = []
        if roll_number == 0:
            return []
        pieces = self.get_pieces()
        other_pieces = self.get_other_pieces()
        if -1 in pieces and -1 + roll_number not in pieces:
            buttons.append(
                ui.Button(
                    label="Новую",
                    style=disnake.ButtonStyle.success,
                    custom_id=ID + "new",
                )
            )
        count = 0
        for i in pieces:
            if i == -1:
                continue
            count += 1
            if i + roll_number not in pieces and i + roll_number < 15:
                if i + roll_number in other_pieces and i + roll_number == 7:
                    continue
                buttons.append(
                    ui.Button(
                        label=str(count),
                        style=disnake.ButtonStyle.success,
                        custom_id=ID + "move_" + str(count),
                    )
                )
        return buttons

    async def update(self):
        await self.original_message.edit(content=str(self))

    def roll(self):
        number_roll = [randint(0, 1) for _ in range(4)]
        string_roll = "".join([ONES_AND_ZEROS[i] for i in number_roll])
        self.last_roll = sum(number_roll)
        return string_roll, self.last_roll

    def make_move(self, piece_number):
        pieces = self.get_pieces()
        other_pieces = self.get_other_pieces()
        count = 0
        for i in range(len(pieces)):
            if pieces[i] == -1:
                continue
            count += 1
            if count == piece_number:
                pieces[i] += self.last_roll
                if 4 <= pieces[i] <= 11 and pieces[i] in other_pieces:
                    other_pieces.remove(pieces[i])
                    other_pieces.insert(0, -1)
                if pieces[i] not in [3, 7, 13]:
                    self.swap_players()
                if pieces[i] == 14:
                    pieces.remove(14)
                pieces.sort()
                break

    def make_move_new(self):
        pieces = self.get_pieces()
        pieces[0] += self.last_roll
        pieces.sort()
        if self.last_roll != 4:
            self.swap_players()


roll_button = ui.Button(
    label="Крутить", style=disnake.ButtonStyle.success, custom_id=ID + "roll"
)
resign_button = ui.Button(
    label="Сдаться", style=disnake.ButtonStyle.danger, custom_id=ID + "resign"
)


class RoyalGameOfUr(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="royal-game-of-ur", description="самая древняя игра в мире"
    )
    async def royal_game_of_ur(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        await inter.response.send_message(
            f"Царская игра Ура с {inter.author.display_name.capitalize()}",
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
        if action == "join":
            if inter.author == inter.message.interaction.author:
                await inter.response.send_message(
                    "Вы не можете играть сами с собой", ephemeral=True
                )
                return
            game = Board(
                inter.author, inter.message.interaction.author, inter.message
            )
            await inter.response.edit_message(str(game), components=[])
            await inter.followup.send(
                f"{game.get_player().mention} за белых, "
                f"{game.get_other_player().mention} за чёрных.\n"
                f"Цель игры - перевести все фишки своего цвета в конечный пункт быстрее своего"
                f" противника. Подробнее: <https://royalur.net/rules#finkel>"
            )
            control_message = await inter.followup.send(
                "Ход белых.", components=[roll_button]
            )
            active_games[control_message.id] = game
        if inter.message.id not in active_games:
            await inter.response.send_message(
                "Эта игра уже закончилась. Начните новую.", ephemeral=True
            )
            return
        if action != "resign":
            game = active_games[inter.message.id]
            if inter.author != game.get_player():
                await inter.response.send_message(
                    "Это не ваш ход.", ephemeral=True
                )
                return
        else:
            game = active_games[inter.message.id]
            if inter.author is game.white_player:
                await inter.response.edit_message(
                    "Белые сдались и чёрные побеждают! Спасибо за игру.",
                    components=[],
                )
            elif inter.author is game.black_player:
                await inter.response.edit_message(
                    "Чёрные сдались и белые побеждают! Спасибо за игру.",
                    components=[],
                )
            else:
                await inter.response.send_message(
                    "Это не ваш ход.", ephemeral=True
                )
                return
            del active_games[inter.message.id]
            return
        if action == "roll":
            dice, roll_number = game.roll()
            if game.is_white():
                color = "Белые"
                other_color = "чёрных."
            else:
                color = "Чёрные"
                other_color = "белых."
            components = game.get_buttons(roll_number)
            if components:
                await inter.response.edit_message(
                    dice + "\n" + color + f" выбили: {roll_number}",
                    components=components,
                )
            elif roll_number == 0:
                game.swap_players()
                await inter.response.edit_message(
                    dice + "\n" + color + " выбили: 0. Какая жалость!\n"
                    "Ход " + other_color,
                    components=[roll_button, resign_button],
                )
            else:
                game.swap_players()
                await inter.response.edit_message(
                    dice + "\n" + color + f" выбили: {roll_number}."
                    f" Возможных ходов нет.\n"
                    "Ход " + other_color,
                    components=[roll_button, resign_button],
                )
        elif "move_" in action:
            first_is_white = game.is_white()
            if first_is_white:
                color = "Белые"
            else:
                color = "Чёрные"
            piece_number = int(action[5:])
            game.make_move(piece_number)
            if game.is_white() == first_is_white:
                other_color = "Они наступили на розетту и ходят ещё раз."
            elif game.is_white():
                other_color = "Ход белых."
            else:
                other_color = "Ход чёрных."
            await game.update()
            if not game.is_game_over():
                await inter.response.edit_message(
                    f"{color} походили.\n" + other_color,
                    components=[roll_button, resign_button],
                )
            else:
                del active_games[inter.message.id]
                await inter.response.edit_message(
                    f"{color} победили! Спасибо за игру.", components=[]
                )
        elif action == "new":
            first_is_white = game.is_white()
            if first_is_white:
                color = "Белые"
            else:
                color = "Чёрные"
            game.make_move_new()
            if game.is_white() == first_is_white:
                other_color = "Они наступили на розетту и ходят ещё раз."
            elif game.is_white():
                other_color = "Ход белых."
            else:
                other_color = "Ход чёрных."
            await game.update()
            if not game.is_game_over():
                await inter.response.edit_message(
                    f"{color} походили.\n" + other_color,
                    components=[roll_button, resign_button],
                )
            else:
                del active_games[inter.message.id]
                await inter.response.edit_message(
                    f"{color} победили! Спасибо за игру.", components=[]
                )


def setup(bot):
    bot.add_cog(RoyalGameOfUr(bot))
