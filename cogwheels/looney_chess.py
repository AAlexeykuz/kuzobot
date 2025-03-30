import asyncio
from random import shuffle

import disnake
from disnake import ui
from disnake.ext import commands

ID = "looney_chess_"
active_games = dict()
resign_button = ui.Button(
    label="Сдаться", style=disnake.ButtonStyle.danger, custom_id=ID + "resign"
)
flip_button = ui.Button(
    label="Перевернуть",
    style=disnake.ButtonStyle.primary,
    custom_id=ID + "flip",
)


class Board:
    def __init__(self, inter: disnake.MessageInteraction):
        players = [inter.author, inter.message.interaction.author]
        shuffle(players)
        self.green, self.purple = players[0], players[1]
        self.current_player = self.green
        self.green_score = 0
        self.purple_score = 0
        self.channel_id = inter.channel_id
        active_games[self.channel_id] = True
        self.inter = inter
        self.components = [flip_button, resign_button]
        self.last_move = None
        self.field = [[0 for _ in range(4)] for _ in range(8)]
        self.flipped = False
        for i in ((1, 2), (2, 1), (2, 2), (5, 1), (5, 2), (6, 1)):
            self.field[i[0]][i[1]] = 1
        for i in ((0, 2), (1, 1), (2, 0), (5, 3), (6, 2), (7, 1)):
            self.field[i[0]][i[1]] = 2
        for i in ((0, 0), (0, 1), (1, 0), (6, 3), (7, 2), (7, 3)):
            self.field[i[0]][i[1]] = 3

    def __str__(self):
        green = ":green_square:"
        purple = ":purple_square:"
        pieces = {
            3: ":white_medium_square:",
            2: ":white_medium_small_square:",
            1: ":white_small_square:",
        }
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
        purple_score = ""
        green_score = ""
        for i in str(self.purple_score):
            purple_score += numbers[int(i)]
        for i in str(self.green_score):
            green_score += numbers[int(i)]
        output = ""
        for row_number in range(8):
            output += numbers[8 - row_number]
            for i in self.field[row_number]:
                if i:
                    output += pieces[i]
                elif row_number < 4:
                    output += purple
                else:
                    output += green
            output += "\n"
        if self.flipped:
            new_output = []
            for i in output.split("\n")[:-1]:
                new_list = []
                for j in i.split(":"):
                    if j:
                        new_list.insert(0, ":" + j + ":")
                new_list.insert(0, new_list[-1])
                del new_list[-1]
                new_output.insert(0, "".join(new_list))
            output = "\n".join(new_output)
        if self.flipped:
            output += (
                "\n:black_large_square::regional_indicator_d::regional_indicator_c:"
                ":regional_indicator_b::regional_indicator_a:\n\n"
            )
        else:
            output += (
                ":black_large_square::regional_indicator_a::regional_indicator_b:"
                ":regional_indicator_c::regional_indicator_d:\n\n"
            )
        if self.flipped:
            output = green_score + "\n\n" + output + purple_score
        else:
            output = purple_score + "\n\n" + output + green_score
        return output

    def flip(self):
        self.flipped = not self.flipped

    async def main_loop(self, bot):
        while self.channel_id in active_games:
            try:
                message = await bot.wait_for("message", timeout=500)
                if (
                    message.author == bot.user
                    or message.channel.id != self.channel_id
                ):
                    continue
                if self.get_player() == message.author:
                    error = self.make_move(message)
                    if error == 1:
                        await self.inter.send("Неверный ход.", ephemeral=True)
                    elif error == 2:
                        await self.inter.send(
                            "Если противник передал вам фигуру, вы не можете "
                            "в тот же ход передвинуть её на тоже место.",
                            ephemeral=True,
                        )
                    elif error == 0:
                        await message.delete()

                        self.swap_players()
                    winner = self.get_a_winner()
                    if winner == self.green:
                        await self.inter.send(
                            "Зелёные победили! Спасибо за игру"
                        )
                        self.game_over()
                    elif winner == self.purple:
                        await self.inter.send(
                            "Фиолетовые победили! Спасибо за игру"
                        )
                        self.game_over()
                    await self.update()
            except asyncio.TimeoutError:
                self.game_over()
                loser = self.current_player
                await self.inter.followup.send(
                    f"{loser.mention} слишком много думал и проиграл."
                )
                await self.update()

    async def update(self):
        await self.inter.message.edit(
            content=str(self), components=self.components
        )

    def is_green(self):
        if self.current_player is self.green:
            return True
        return False

    def swap_players(self):
        if self.is_green():
            self.current_player = self.purple
        else:
            self.current_player = self.green

    def make_move(self, message):
        letters = ["a", "b", "c", "d"]
        numbers = ["8", "7", "6", "5", "4", "3", "2", "1"]
        text = message.content.split(" ")
        coords = []
        if len(text) < 2:
            return None
        for i in text[:2]:
            x = i[1]
            y = i[0].lower()
            if x not in numbers or y not in letters:
                return None
            coords.append((numbers.index(x), letters.index(y)))
        print(coords, self.last_move)
        if not self.is_on_their_side(coords[0]) or coords[
            1
        ] not in self.get_possible_moves(coords[0]):
            return 1
        if coords[::-1] == self.last_move:
            return 2
        if (
            self.is_on_their_side(coords[1])
            and self.field[coords[1][0]][coords[1][1]]
        ):
            self.field[coords[1][0]][coords[1][1]] += 1
            self.last_move = None
        elif self.is_on_their_side(coords[1]):
            self.field[coords[1][0]][coords[1][1]] = self.field[coords[0][0]][
                coords[0][1]
            ]
            self.last_move = None
        else:
            if self.is_green():
                self.green_score += self.field[coords[1][0]][coords[1][1]]
            else:
                self.purple_score += self.field[coords[1][0]][coords[1][1]]
            self.field[coords[1][0]][coords[1][1]] = self.field[coords[0][0]][
                coords[0][1]
            ]
            self.last_move = coords
        self.field[coords[0][0]][coords[0][1]] = 0
        return 0

    def is_on_their_side(self, coords):
        return not (
            (self.is_green() and coords[0] < 4)
            or (not self.is_green() and coords[0] > 3)
        )

    def get_player(self):
        return self.current_player

    def get_a_winner(self):
        if not any([any(i) for i in self.field[:4]]):
            if self.purple_score >= self.green_score:
                return self.purple
            return self.green
        if not any([any(i) for i in self.field[4:]]):
            if self.green_score >= self.purple_score:
                return self.green
            return self.purple

    def game_over(self):
        self.components = []
        del active_games[self.channel_id]

    # Функция не учитывает правило, что нельзя повторять позиции. Это делается в make_move
    def get_possible_moves(self, coords):
        if self.is_green():
            no_queens = not any(
                [any(map(lambda x: x == 3, i)) for i in self.field[4:]]
            )
            no_drones = not any(
                [any(map(lambda x: x == 2, i)) for i in self.field[4:]]
            )
        else:
            no_queens = not any(
                [any(map(lambda x: x == 3, i)) for i in self.field[:4]]
            )
            no_drones = not any(
                [any(map(lambda x: x == 2, i)) for i in self.field[:4]]
            )
        row = coords[0]
        col = coords[1]
        piece = self.field[row][col]
        possible_moves = []
        if piece == 1:
            for i in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                if 0 <= row + i[0] <= 7 and 0 <= col + i[1] <= 3:
                    if (
                        not self.field[row + i[0]][col + i[1]]
                        or not self.is_on_their_side((row + i[0], col + i[1]))
                        or (
                            self.is_on_their_side((row + i[0], col + i[1]))
                            and self.field[row + i[0]][col + i[1]] == 1
                            and no_drones
                        )
                    ):
                        possible_moves.append((row + i[0], col + i[1]))
        elif piece == 2:
            # up
            for i in range(1, 3):
                if row + i > 7:
                    break
                if self.field[row + i][col]:
                    if self.is_on_their_side((row + i, col)):
                        if self.field[row + i][col] == 2 and no_queens:
                            possible_moves.append((row + i, col))
                        break
                    possible_moves.append((row + i, col))
                    break
                possible_moves.append((row + i, col))
            # down
            for i in range(1, 3):
                if row - i < 0:
                    break
                if self.field[row - i][col]:
                    if self.is_on_their_side((row - i, col)):
                        if self.field[row - i][col] == 2 and no_queens:
                            possible_moves.append((row - i, col))
                        break
                    possible_moves.append((row - i, col))
                    break
                possible_moves.append((row - i, col))
            # right
            for i in range(1, 3):
                if col + i > 3:
                    break
                if self.field[row][col + i]:
                    if self.is_on_their_side((row, col + i)):
                        if self.field[row][col + i] == 2 and no_queens:
                            possible_moves.append((row, col + i))
                        break
                    possible_moves.append((row, col + i))
                    break
                possible_moves.append((row, col + i))
            # left
            for i in range(1, 3):
                if col - i < 0:
                    break
                if self.field[row][col - i]:
                    if self.is_on_their_side((row, col - i)):
                        if self.field[row][col - i] == 2 and no_queens:
                            possible_moves.append((row, col - i))
                        break
                    possible_moves.append((row, col - i))
                    break
                possible_moves.append((row, col - i))
        elif piece == 3:
            # up
            for i in range(1, 8):
                if row + i > 7:
                    break
                if self.field[row + i][col]:
                    if self.is_on_their_side((row + i, col)):
                        break
                    possible_moves.append((row + i, col))
                    break
                possible_moves.append((row + i, col))
            # down
            for i in range(1, 8):
                if row - i < 0:
                    break
                if self.field[row - i][col]:
                    if self.is_on_their_side((row - i, col)):
                        break
                    possible_moves.append((row - i, col))
                    break
                possible_moves.append((row - i, col))
            # right
            for i in range(1, 4):
                if col + i > 3:
                    break
                if self.field[row][col + i]:
                    if self.is_on_their_side((row, col + i)):
                        break
                    possible_moves.append((row, col + i))
                    break
                possible_moves.append((row, col + i))
            # left
            for i in range(1, 4):
                if col - i < 0:
                    break
                if self.field[row][col - i]:
                    if self.is_on_their_side((row, col - i)):
                        break
                    possible_moves.append((row, col - i))
                    break
                possible_moves.append((row, col - i))
            # right-up
            for i in range(1, 4):
                if row + i > 7 or col + i > 3:
                    break
                if self.field[row + i][col + i]:
                    if self.is_on_their_side((row + i, col + i)):
                        break
                    possible_moves.append((row + i, col + i))
                    break
                possible_moves.append((row + i, col + i))
            # right-down
            for i in range(1, 4):
                if row - i < 0 or col + i > 3:
                    break
                if self.field[row - i][col + i]:
                    if self.is_on_their_side((row - i, col + i)):
                        break
                    possible_moves.append((row - i, col + i))
                    break
                possible_moves.append((row - i, col + i))
            # left-up
            for i in range(1, 4):
                if row + i > 7 or col - i < 0:
                    break
                if self.field[row + i][col - i]:
                    if self.is_on_their_side((row + i, col - i)):
                        break
                    possible_moves.append((row + i, col - i))
                    break
                possible_moves.append((row + i, col - i))
            # left-down
            for i in range(1, 4):
                if row - i < 0 or col - i < 0:
                    break
                if self.field[row - i][col - i]:
                    if self.is_on_their_side((row - i, col - i)):
                        break
                    possible_moves.append((row - i, col - i))
                    break
                possible_moves.append((row - i, col - i))
        return possible_moves

    def get_players(self):
        return self.green, self.purple


class LooneyChess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="martian-chess", description="лунные шахматы")
    async def looney_chess(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            f"Игра в Лунные шахматы с {inter.author.mention}",
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
            # if inter.author == inter.message.interaction.author:
            #     await inter.response.send_message('Вы не можете играть сами с собой', ephemeral=True)
            #     return
            if inter.channel_id in active_games:
                await inter.response.send_message(
                    "Игра уже началась в этом канале", ephemeral=True
                )
                return
            game = Board(inter)
            active_games[inter.channel_id] = game
            await inter.response.edit_message(
                str(game), components=[flip_button, resign_button]
            )
            green, purple = game.get_players()
            await inter.channel.send(
                f"За зелёных играет {green.mention}, за фиолетовых - {purple.mention}. "
                "Правила: <https://www.looneylabs.com/sites/default/"
                "files/pyramid_rules/Rules.MartianChess.pdf>\n"
                "Чтобы походить, напишите: прошлая координата, пробел, желаемая координата. "
                "Например: B3 A4\n"
                "Первыми ходят зелёные."
            )
            await game.main_loop(self.bot)
        elif action == "resign":
            game = active_games[inter.channel_id]
            if inter.author not in game.get_players():
                await inter.response.send_message(
                    "Это не ваша игра.", ephemeral=True
                )
                return
            game.game_over()
            await game.update()
            if inter.author == game.green:
                await inter.response.send_message(
                    "Зелёные сдаются. Спасибо за игру!"
                )
            elif inter.author == game.purple:
                await inter.response.send_message(
                    "Фиолетовые сдаются. Спасибо за игру!"
                )
        elif action == "flip":
            game = active_games[inter.channel_id]
            if inter.author not in game.get_players():
                await inter.response.send_message(
                    "Это не ваша игра.", ephemeral=True
                )
                return
            game.flip()
            await inter.response.edit_message(
                str(game), components=[flip_button, resign_button]
            )


def setup(bot):
    bot.add_cog(LooneyChess(bot))
