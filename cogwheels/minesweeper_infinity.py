from random import random

import disnake
from disnake import ui
from disnake.ext import commands

ID = "minesweeper_infinity_"
invisible = "ㅤ"

active_games = dict()
numbers = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]


def save(player_id: int, score: int, density: float) -> None:
    records = dict()
    for line in (
        open("databases/minesweeper_records.txt", encoding="utf-8")
        .read()
        .split("\n")
    ):
        if not line:
            continue
        some_player_id, some_score, some_density = line.split(" ")
        records[int(some_player_id)] = (int(some_score), float(some_density))
    if player_id in records:
        records[player_id] = (max(score, records[player_id][0]), density)
    else:
        records[player_id] = (score, density)
    with open(
        "databases/minesweeper_records.txt", "w", encoding="utf-8"
    ) as file:
        for i in records:
            file.write(f"{i} {records[i][0]} {records[i][1]}\n")


class Cell:
    def __init__(self, density):
        self.bomb = random() < density
        self.flag = False
        self.visible = False

    def open(self):
        self.visible = True

    def switch_flag(self):
        self.flag = not self.flag

    def is_bomb(self):
        return self.bomb

    def is_open(self):
        return self.visible

    def is_flagged(self):
        return self.flag


class ZeroCell(Cell):
    def __init__(self):
        super().__init__(0)
        self.visible = True


class Game:
    def __init__(self, density, player):
        self.coefficient = 20000
        self.player = player
        self.density = density
        self.field = dict()
        self.field[-2] = {0: ZeroCell()}
        self.field[-1] = {0: ZeroCell()}
        self.field[0] = {
            -2: ZeroCell(),
            -1: ZeroCell(),
            0: ZeroCell(),
            1: ZeroCell(),
            2: ZeroCell(),
        }
        self.field[1] = {0: ZeroCell()}
        self.field[2] = {0: ZeroCell()}
        self.x = -2
        self.y = -1
        self.radius = 10
        self.game_over = False
        self.mode = "move"
        self.flag_style = disnake.ButtonStyle.secondary
        self.explored_space = None
        self.score = 0
        self.correct_flags = 0
        self.incorrect_flags = 0
        self.generate_chunk(self.radius)
        self.message = None

    def __str__(self):
        output = ""
        for y in range(self.y + 3, self.y - 1, -1):
            for x in range(self.x, self.x + 5):
                if self.field[x][y].is_open():
                    if self.field[x][y].is_bomb():
                        output += "B"
                    else:
                        output += str(self.count_bombs(x, y))
                else:
                    output += "#"
            output += "\n"
        return output

    def set_message(self, msg: disnake.Message):
        self.message = msg

    def get_buttons(self):
        buttons = []
        if self.is_game_over():
            disable = True
        else:
            disable = False
        for y in range(self.y + 3, self.y - 1, -1):
            for x in range(self.x, self.x + 5):
                if self.field[x][y].is_open():
                    if self.field[x][y].is_bomb():
                        buttons.append(
                            ui.Button(
                                emoji="💥",
                                style=disnake.ButtonStyle.danger,
                                disabled=True,
                            )
                        )
                    else:
                        count = numbers[self.count_bombs(x, y)]
                        buttons.append(
                            ui.Button(
                                emoji=count,
                                style=disnake.ButtonStyle.primary,
                                custom_id=ID
                                + "known_"
                                + str(x - self.x)
                                + str(y - self.y),
                                disabled=disable,
                            )
                        )
                elif self.field[x][y].is_flagged():
                    buttons.append(
                        ui.Button(
                            emoji="🚩",
                            style=disnake.ButtonStyle.success,
                            custom_id=ID
                            + "mystery_"
                            + str(x - self.x)
                            + str(y - self.y),
                            disabled=disable,
                        )
                    )
                else:
                    buttons.append(
                        ui.Button(
                            label=invisible,
                            style=disnake.ButtonStyle.secondary,
                            custom_id=ID
                            + "mystery_"
                            + str(x - self.x)
                            + str(y - self.y),
                            disabled=disable,
                        )
                    )
        buttons.extend(
            [
                ui.Button(
                    label="🚩",
                    style=self.flag_style,
                    custom_id=ID + "flag",
                    disabled=disable,
                )
            ]
        )
        return buttons

    def generate_cell(self, x, y):
        for x_offset in (-1, 0, 1):
            for y_offset in (-1, 0, 1):
                new_x = x + x_offset
                new_y = y + y_offset
                if new_x not in self.field:
                    self.field[new_x] = dict()
                if new_y not in self.field[new_x]:
                    self.field[new_x][new_y] = Cell(
                        self.density + self.score / self.coefficient
                    )

    def generate_chunk(self, radius):
        for x in range(self.x + 2 - radius, self.x + 2 + radius):
            for y in range(self.y + 1 - radius, self.y + 1 + radius):
                self.generate_cell(x, y)
        for _ in range(radius):
            for x in range(self.x + 2 - radius, self.x + 2 + radius):
                for y in range(self.y + 1 - radius, self.y + 1 + radius):
                    if (
                        self.count_bombs(x, y) == 0
                        and self.field[x][y].is_open()
                    ):
                        self.fully_open(x, y)

    def open_everything(self):
        self.explored_space = self.count_cells() - 1
        for y in range(self.y + 3, self.y - 1, -1):
            for x in range(self.x, self.x + 5):
                self.field[x][y].open()
                if self.field[x][y].is_bomb() and self.field[x][y].is_flagged():
                    self.field[x][y].switch_flag()

    def count_bombs(self, x, y):
        count = 0
        for x_offset in (-1, 0, 1):
            for y_offset in (-1, 0, 1):
                if self.field[x + x_offset][y + y_offset].is_bomb():
                    count += 1
        return count

    def fully_open(self, x, y):
        for x_offset in (-1, 0, 1):
            for y_offset in (-1, 0, 1):
                new_x = x + x_offset
                new_y = y + y_offset
                if not self.field[new_x][new_y].is_open():
                    self.field[new_x][new_y].open()
                    self.generate_cell(new_x, new_y)
                    if not self.is_game_over():
                        self.score += self.calculate_score(new_x, new_y)

    def calculate_score(self, x, y):
        n = self.count_bombs(x, y)
        if n == 0:
            return 0
        if n == 1:
            score = 1
        elif n == 2:
            score = 2
        elif n == 3:
            score = 7
        elif n == 4:
            score = 30
        elif n == 5:
            score = 150
        elif n == 6:
            score = 500
        elif n == 7:
            score = 5000
        else:
            score = 50000
        return score * 15 * (self.density + self.score / self.coefficient) ** 2

    def move(self, delta_x, delta_y):
        self.x += delta_x
        self.y += delta_y
        self.generate_chunk(self.radius)

    def make_move(self, x, y):
        if not self.field[x][y].is_flagged():
            self.field[x][y].open()
            if self.field[x][y].is_bomb():
                self.game_over = True
                self.open_everything()
            else:
                self.score += self.count_bombs(x, y) * 10 * self.density
        self.generate_chunk(self.radius)

    def flag(self, x, y):
        self.field[x][y].switch_flag()
        if self.field[x][y].is_flagged():
            if self.field[x][y].is_bomb():
                self.correct_flags += 1
            else:
                self.incorrect_flags += 1
        elif self.field[x][y].is_bomb():
            self.correct_flags -= 1
        else:
            self.incorrect_flags -= 1

    def switch_mode(self):
        if self.mode == "move":
            self.mode = "flag"
            self.flag_style = disnake.ButtonStyle.success
        else:
            self.mode = "move"
            self.flag_style = disnake.ButtonStyle.secondary

    def get_coords(self):
        return self.x, self.y

    def get_mode(self):
        return self.mode

    def is_game_over(self):
        return self.game_over

    def get_content(self):
        if not self.explored_space:
            explored = self.count_cells()
        else:
            explored = self.explored_space
        score = (
            int(self.score)
            + round(explored * 5 / 3 * self.density)
            + (self.correct_flags + self.incorrect_flags) * 5
        )
        return (
            f"X: {self.x + 2} Y: {self.y + 1}\nОЧКИ: {score}, "
            f"ИССЛЕДОВАНО: {explored}"
        )

    def get_score(self):
        return self.score

    def count_cells(self):
        count = 0
        for i in self.field:
            for j in self.field[i]:
                if self.field[i][j].is_open():
                    count += 1
        return count


class MinesweeperInfinityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_records(self) -> str:
        records = list()
        for line in (
            open("databases/minesweeper_records.txt", encoding="utf-8")
            .read()
            .split("\n")
        ):
            if not line:
                continue
            records.append(
                (
                    int(line.split(" ")[1]),
                    float(line.split(" ")[2]),
                    int(line.split(" ")[0]),
                )
            )
        records.sort(reverse=True)
        top_10 = ""
        count = 0
        for i in records:
            try:
                user = await self.bot.fetch_user(i[2])
                top_10 += f"{user.name}: {i[0]} ({i[1]})\n"
                count += 1
            except Exception:
                continue
            if count >= 10:
                break
        return top_10

    @commands.slash_command(
        name="minesweeper-universe",
        description="бесконечный сапёр с открытым миром",
    )
    async def minesweeper_infinity(
        self, inter: disnake.ApplicationCommandInteraction, density: float
    ):
        if density > 0.5:
            await inter.response.send_message(
                "Слишком большая плотность бомб. Рекомендуемое значение -"
                " 0.17.",
                ephemeral=True,
            )
            return
        if density < 0:
            await inter.response.send_message(
                "Некорректная плотность бомб", ephemeral=True
            )
            return
        if inter.author.id in active_games:
            await inter.response.send_message(
                "Вы уже начали игру в каком-то из каналов. "
                "Хотите начать новую?",
                ephemeral=True,
                components=[
                    ui.Button(
                        label="Новая игра",
                        style=disnake.ButtonStyle.primary,
                        custom_id=ID + "restart_" + str(density),
                    )
                ],
            )
            return
        game = Game(density, inter.author)
        components = game.get_buttons()
        content = game.get_content()
        await inter.response.send_message(
            content=content, components=components
        )
        message = await inter.original_response()
        game.set_message(message)
        active_games[message.id] = game

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith(ID):
            return
        if inter.message.id not in active_games:
            await inter.response.send_message(
                "Эта игра уже закончилась.", ephemeral=True
            )
            return
        action = inter.component.custom_id[len(ID) :]
        game = active_games[inter.message.id]
        if game.player != inter.author:
            await inter.response.send_message(
                "Это не ваша игра.", ephemeral=True
            )
            return
        if action == "flag":
            game.switch_mode()
            components = game.get_buttons()
            content = game.get_content()
            await inter.response.edit_message(
                content=content, components=components
            )
        elif "known" in action:
            button_x = int(action[-2]) - 2
            button_y = int(action[-1])
            if button_y > 1:
                button_y -= 1
            else:
                button_y -= 2
            game.move(button_x, button_y)
            components = game.get_buttons()
            content = game.get_content()
            await inter.response.edit_message(
                content=content, components=components
            )
        elif "mystery" in action:
            x, y = game.get_coords()
            x = int(action[-2]) + x
            y = int(action[-1]) + y
            if game.get_mode() == "flag":
                game.flag(x, y)
                components = game.get_buttons()
                content = game.get_content()
                await inter.response.edit_message(
                    content=content, components=components
                )
            else:
                game.make_move(x, y)
                components = game.get_buttons()
                content = game.get_content()
                await inter.response.edit_message(
                    content=content, components=components
                )
        if game.is_game_over():
            mine_score = int(game.score)  # дальше мне уже было на всё пофек
            correct_flags = game.correct_flags
            incorrect_flags = game.incorrect_flags
            explored_space = game.explored_space
            explored_score = round(explored_space * 5 / 3 * game.density)
            final_score = (
                mine_score
                + explored_score
                + correct_flags * 5
                - incorrect_flags * 15
            )
            save(inter.author.id, final_score, game.density)
            await inter.channel.send(
                content=f"Спасибо за игру, {inter.author.mention}!\n"
                f"Очки за сложность: +{mine_score}\n"
                f"Всего открыто полей: {explored_space} "
                f"(+{explored_score})\n"
                f"Правильных флажков: {correct_flags} (+{correct_flags * 5})\n"
                f"Неправильных флажков: {incorrect_flags} "
                f"(-{incorrect_flags * 15})\n"
                f"====================\n"
                f"Всего очков: {final_score} при плотности {game.density}\n"
                f"```\nРекорды\n{await self.get_records()}```\n"
            )
            del active_games[game.message.id]


def setup(bot):
    bot.add_cog(MinesweeperInfinityCog(bot))
