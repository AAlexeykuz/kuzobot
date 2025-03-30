import random
from time import sleep

import disnake
from disnake import ui
from disnake.ext import commands

ID = "tetris_"

invisible = "ㅤ"
active_games = dict()
emojis = "🔽🔼◀️▶️"


def save(player_id: int, score: int) -> None:
    records = dict()
    for line in (
        open("databases/tetris_records.txt", encoding="utf-8")
        .read()
        .split("\n")
    ):
        if not line:
            continue
        some_player_id, some_score = line.split(" ")
        records[int(some_player_id)] = int(some_score)
    if player_id in records:
        records[player_id] = max(score, records[player_id])
    else:
        records[player_id] = score
    with open("databases/tetris_records.txt", "w", encoding="utf-8") as file:
        for i in records:
            file.write(f"{i} {records[i]}\n")


class Tetris:
    def __init__(self, game_message: disnake.Message, player: disnake.Member):
        self.player = player
        self.game_message = game_message
        self.components = [
            ui.Button(
                emoji="⏪",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "big_left",
            ),
            ui.Button(
                emoji="◀️",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "left",
            ),
            ui.Button(
                emoji="🔽",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "small_down",
            ),
            ui.Button(
                emoji="▶️",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "right",
            ),
            ui.Button(
                emoji="⏩",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "big_right",
            ),
            ui.Button(
                label=invisible,
                style=disnake.ButtonStyle.secondary,
                disabled=True,
            ),
            ui.Button(
                emoji="↪️",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "anticlockwise",
            ),
            ui.Button(
                emoji="⏬",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "down",
            ),
            ui.Button(
                emoji="↩️",
                style=disnake.ButtonStyle.primary,
                custom_id=ID + "clockwise",
            ),
            ui.Button(
                label=invisible,
                style=disnake.ButtonStyle.secondary,
                disabled=True,
            ),
        ]
        self.field = [[0 for _ in range(10)] for _ in range(18)]
        self.speed = 4
        self.game_over = False
        self.already_updated = False
        self.down = False
        self.current_piece = None
        self.current_piece_color = None
        self.current_coords = None
        self.current_center = None
        self.current_rotation = 0
        self.next_piece = None
        self.next_piece_color = None
        self.next_piece_image = None
        self.generate_piece()
        self.put_piece()
        self.actions = []
        self.counter = 0
        self.score = 0
        self.message_show = 0
        self.message = ""

    def __str__(self):
        colors = ["⬛", "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫"]
        string = ""
        for i in range(len(self.field)):
            if self.game_over and i in [7, 8, 9]:
                if i == 8:
                    string += (
                        "⏺️:regional_indicator_g::regional_indicator_a::regional_indicator_m:"
                        ":regional_indicator_e::regional_indicator_o::regional_indicator_v:"
                        ":regional_indicator_e::regional_indicator_r:⏺️"
                    )
                else:
                    string += "⏺️" * 10
            else:
                for j in self.field[i]:
                    string += colors[j]
            if i == 4 and self.message_show >= self.counter:
                string += " " * 6 + self.message
            if i == 6:
                string += " " * 6 + "NEXT:"
            elif i in [7, 8, 9, 10]:
                string += " " * 6 + "".join(
                    [colors[j] for j in self.next_piece_image[i - 7]]
                )
            elif i == 11:
                string += " " * 6 + "SCORE:"
            elif i == 12:
                string += " " * 6 + str(int(self.score))
            string += "\n"
        return string

    def generate_piece(self):
        self.next_piece = random.choice(["I", "J", "L", "O", "S", "T", "Z"])
        colors = {"I": 5, "J": 2, "L": 7, "O": 3, "S": 4, "T": 6, "Z": 1}
        c = colors[self.next_piece]
        self.next_piece_color = c
        if self.next_piece == "I":
            self.next_piece_image = [
                [0, 0, c, 0],
                [0, 0, c, 0],
                [0, 0, c, 0],
                [0, 0, c, 0],
            ]
        elif self.next_piece == "J":
            self.next_piece_image = [
                [0, 0, 0, 0],
                [0, c, 0, 0],
                [0, c, c, c],
                [0, 0, 0, 0],
            ]
        elif self.next_piece == "L":
            self.next_piece_image = [
                [0, 0, 0, 0],
                [0, 0, 0, c],
                [0, c, c, c],
                [0, 0, 0, 0],
            ]
        elif self.next_piece == "O":
            self.next_piece_image = [
                [0, 0, 0, 0],
                [0, c, c, 0],
                [0, c, c, 0],
                [0, 0, 0, 0],
            ]
        elif self.next_piece == "S":
            self.next_piece_image = [
                [0, 0, 0, 0],
                [0, 0, c, c],
                [0, c, c, 0],
                [0, 0, 0, 0],
            ]
        elif self.next_piece == "T":
            self.next_piece_image = [
                [0, 0, 0, 0],
                [0, c, c, c],
                [0, 0, c, 0],
                [0, 0, 0, 0],
            ]
        else:
            self.next_piece_image = [
                [0, 0, 0, 0],
                [0, c, c, 0],
                [0, 0, c, c],
                [0, 0, 0, 0],
            ]

    def put_piece(self):
        self.current_rotation = 0
        if self.next_piece == "I":
            coords = [[0, 3], [0, 4], [0, 5], [0, 6]]
            self.current_center = [-1, 3]
        elif self.next_piece == "J":
            coords = [[0, 3], [1, 3], [1, 4], [1, 5]]
            self.current_center = [0, 3]
        elif self.next_piece == "L":
            coords = [[0, 5], [1, 3], [1, 4], [1, 5]]
            self.current_center = [0, 3]
        elif self.next_piece == "O":
            coords = [[0, 4], [0, 5], [1, 4], [1, 5]]
            self.current_center = [0, 4]
        elif self.next_piece == "S":
            coords = [[0, 4], [0, 5], [1, 3], [1, 4]]
            self.current_center = [0, 3]
        elif self.next_piece == "T":
            coords = [[0, 3], [0, 4], [0, 5], [1, 4]]
            self.current_center = [-1, 3]
        else:
            coords = [[0, 3], [0, 4], [1, 4], [1, 5]]
            self.current_center = [0, 3]
        for i in coords:
            if self.field[i[0]][i[1]]:
                self.do_game_over()
        if not self.game_over:
            self.current_piece = self.next_piece
            self.current_piece_color = self.next_piece_color
            self.current_coords = coords
            for i in coords:
                self.field[i[0]][i[1]] = self.next_piece_color
            self.generate_piece()

    def do_game_over(self):
        self.game_over = True
        for i in self.components:
            i.disabled = True

    def update_movement(self):
        for action in self.actions.copy():
            if action == "left":
                self.left()
            elif action == "right":
                self.right()
            elif action == "big_left":
                while True:
                    if self.left():
                        break
            elif action == "big_right":
                while True:
                    if self.right():
                        break
            elif action == "clockwise":
                self.rotate(1)
            elif action == "anticlockwise":
                self.rotate(-1)
            elif action == "small_down":
                self.update_gravity()
                self.score += 0.5
            elif action == "down":
                while True:
                    if self.update_gravity():
                        break
                    self.score += 0.5
            self.actions.remove(action)

    def update_gravity(self):
        for i in self.current_coords:
            if i[0] >= 17:
                self.score += i[0] / self.speed
                self.put_piece()
                return True
            if (
                self.field[i[0] + 1][i[1]]
                and [i[0] + 1, i[1]] not in self.current_coords
            ):
                self.score += i[0] / self.speed
                self.put_piece()
                return True
        for i in range(4):
            self.field[self.current_coords[i][0]][self.current_coords[i][1]] = 0
        self.current_center[0] += 1
        for i in range(4):
            self.current_coords[i][0] += 1
            self.field[self.current_coords[i][0]][self.current_coords[i][1]] = (
                self.current_piece_color
            )

    async def update_image(self):
        await self.game_message.edit(str(self), components=self.components)

    def left(self):
        if self.on_border() == -1:
            return True
        for i in self.current_coords:
            if (
                self.field[i[0]][i[1] - 1]
                and [i[0], i[1] - 1] not in self.current_coords
            ):
                return True
        for i in range(4):
            self.field[self.current_coords[i][0]][self.current_coords[i][1]] = 0
        self.current_center[1] -= 1
        for i in range(4):
            self.current_coords[i][1] -= 1
            self.field[self.current_coords[i][0]][self.current_coords[i][1]] = (
                self.current_piece_color
            )
        self.on_border()

    def right(self):
        if self.on_border() == 1:
            return True
        for i in self.current_coords:
            if (
                self.field[i[0]][i[1] + 1]
                and [i[0], i[1] + 1] not in self.current_coords
            ):
                return True
        for i in range(4):
            self.field[self.current_coords[i][0]][self.current_coords[i][1]] = 0
        self.current_center[1] += 1
        for i in range(4):
            self.current_coords[i][1] += 1
            self.field[self.current_coords[i][0]][self.current_coords[i][1]] = (
                self.current_piece_color
            )
        self.on_border()

    def on_border(self):
        for i in range(4):
            if self.current_coords[i][1] <= 0:
                return -1
            if self.current_coords[i][1] >= 9:
                return 1

    def rotate(self, number):
        if number == 0 or self.current_piece == "O":
            return 1
        self.current_rotation += number
        original_center = self.current_center
        if self.current_piece == "I":
            self.current_center[0] = max(self.current_center[0], 0)
            if self.current_center[1] < 0:
                self.current_center[1] = 0
            elif self.current_center[1] > 6:
                self.current_center[1] = 6
            y, x = self.current_center
            if self.current_rotation % 4 == 0:
                new_coords = [
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                    [y + 1, x + 3],
                ]
            elif self.current_rotation % 4 == 1:
                new_coords = [
                    [y, x + 2],
                    [y + 1, x + 2],
                    [y + 2, x + 2],
                    [y + 3, x + 2],
                ]
            elif self.current_rotation % 4 == 2:
                new_coords = [
                    [y + 2, x],
                    [y + 2, x + 1],
                    [y + 2, x + 2],
                    [y + 2, x + 3],
                ]
            else:
                new_coords = [
                    [y, x + 1],
                    [y + 1, x + 1],
                    [y + 2, x + 1],
                    [y + 3, x + 1],
                ]
            for i in new_coords:
                if self.field[i[0]][i[1]] and i not in self.current_coords:
                    self.current_center = original_center
                    self.current_rotation -= number
                    return None
            self.change_coords(new_coords)
        elif self.current_piece == "J":
            if self.current_center[1] < 0:
                self.current_center[1] = 0
            elif self.current_center[1] > 7:
                self.current_center[1] = 7
            y, x = self.current_center
            if self.current_rotation % 4 == 0:
                new_coords = [
                    [y, x],
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                ]
            elif self.current_rotation % 4 == 1:
                new_coords = [
                    [y, x + 1],
                    [y, x + 2],
                    [y + 1, x + 1],
                    [y + 2, x + 1],
                ]
            elif self.current_rotation % 4 == 2:
                new_coords = [
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                    [y + 2, x + 2],
                ]
            else:
                new_coords = [
                    [y, x + 1],
                    [y + 1, x + 1],
                    [y + 2, x],
                    [y + 2, x + 1],
                ]
            for i in new_coords:
                if self.field[i[0]][i[1]] and i not in self.current_coords:
                    self.current_center = original_center
                    self.current_rotation -= number
                    return None
            self.change_coords(new_coords)
        elif self.current_piece == "L":
            if self.current_center[1] < 0:
                self.current_center[1] = 0
            elif self.current_center[1] > 7:
                self.current_center[1] = 7
            y, x = self.current_center
            if self.current_rotation % 4 == 0:
                new_coords = [
                    [y, x + 2],
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                ]
            elif self.current_rotation % 4 == 1:
                new_coords = [
                    [y, x + 1],
                    [y + 1, x + 1],
                    [y + 2, x + 1],
                    [y + 2, x + 2],
                ]
            elif self.current_rotation % 4 == 2:
                new_coords = [
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                    [y + 2, x],
                ]
            else:
                new_coords = [
                    [y, x],
                    [y, x + 1],
                    [y + 1, x + 1],
                    [y + 2, x + 1],
                ]
            for i in new_coords:
                if self.field[i[0]][i[1]] and i not in self.current_coords:
                    self.current_center = original_center
                    self.current_rotation -= number
                    return None
            self.change_coords(new_coords)
        elif self.current_piece == "S":
            if self.current_center[1] < 0:
                self.current_center[1] = 0
            elif self.current_center[1] > 7:
                self.current_center[1] = 7
            y, x = self.current_center
            if self.current_rotation % 4 == 0:
                new_coords = [
                    [y, x + 1],
                    [y, x + 2],
                    [y + 1, x],
                    [y + 1, x + 1],
                ]
            elif self.current_rotation % 4 == 1:
                new_coords = [
                    [y, x + 1],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                    [y + 2, x + 2],
                ]
            elif self.current_rotation % 4 == 2:
                new_coords = [
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                    [y + 2, x],
                    [y + 2, x + 1],
                ]
            else:
                new_coords = [
                    [y, x],
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 2, x + 1],
                ]
            for i in new_coords:
                if self.field[i[0]][i[1]] and i not in self.current_coords:
                    self.current_center = original_center
                    self.current_rotation -= number
                    return None
            self.change_coords(new_coords)
        elif self.current_piece == "T":
            self.current_center[0] = max(self.current_center[0], 0)
            if self.current_center[1] < 0:
                self.current_center[1] = 0
            elif self.current_center[1] > 7:
                self.current_center[1] = 7
            y, x = self.current_center
            if self.current_rotation % 4 == 0:
                new_coords = [
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                    [y + 2, x + 1],
                ]
            elif self.current_rotation % 4 == 1:
                new_coords = [
                    [y, x + 1],
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 2, x + 1],
                ]
            elif self.current_rotation % 4 == 2:
                new_coords = [
                    [y, x + 1],
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                ]
            else:
                new_coords = [
                    [y, x + 1],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                    [y + 2, x + 1],
                ]
            for i in new_coords:
                if self.field[i[0]][i[1]] and i not in self.current_coords:
                    self.current_center = original_center
                    self.current_rotation -= number
                    return None
            self.change_coords(new_coords)
        else:
            if self.current_center[1] < 0:
                self.current_center[1] = 0
            elif self.current_center[1] > 7:
                self.current_center[1] = 7
            y, x = self.current_center
            if self.current_rotation % 4 == 0:
                new_coords = [
                    [y, x],
                    [y, x + 1],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                ]
            elif self.current_rotation % 4 == 1:
                new_coords = [
                    [y, x + 2],
                    [y + 1, x + 1],
                    [y + 1, x + 2],
                    [y + 2, x + 1],
                ]
            elif self.current_rotation % 4 == 2:
                new_coords = [
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 2, x + 1],
                    [y + 2, x + 2],
                ]
            else:
                new_coords = [
                    [y, x + 1],
                    [y + 1, x],
                    [y + 1, x + 1],
                    [y + 2, x],
                ]
            for i in new_coords:
                if self.field[i[0]][i[1]] and i not in self.current_coords:
                    self.current_center = original_center
                    self.current_rotation -= number
                    return None
            self.change_coords(new_coords)
        return True

    def change_coords(self, coords):
        for i in self.current_coords:
            self.field[i[0]][i[1]] = 0
        for i in coords:
            self.field[i[0]][i[1]] = self.current_piece_color
        self.current_coords = coords

    async def main_loop_v1(self):
        while not self.game_over:
            self.update_movement()
            if self.counter % self.speed == self.speed - 1:
                self.update_gravity()
                self.speedup()
            self.count()
            await self.update_image()
            if self.delete_lines():
                await self.update_image()

    async def main_loop_v2(self):
        while not self.game_over:
            sleep(0.78)
            self.update_gravity()
            self.delete_lines()
            await self.update_image()

    # async def main_loop_v3(self):
    #     while not self.game_over:
    #         self.update_movement()
    #         if self.counter % self.speed == self.speed - 1:
    #             self.update_gravity()
    #             self.speedup()
    #         self.count()
    #         await game.update_image()
    #         if game.delete_lines():
    #             await game.update_image()
    #         await asyncio.sleep(1 / 60)

    # def add_left(self, number):
    #     self.left_movements += number
    #
    # def add_right(self, number):
    #     self.right_movements += number
    #
    # def set_rotate(self, number):
    #     self.rotate_movement = number

    def add_action(self, action):
        self.actions.append(action)

    #
    # def get_down(self):
    #     self.down = True

    def count(self):
        self.counter += 1

    def speedup(self):
        if self.score > 5000 and self.speed == 4:
            self.speed = 3
            self.message = "SPEED UP!"
            self.message_show = self.counter + 7
        elif self.score > 15000 and self.speed == 3:
            self.speed = 2
            self.message = "SPEED UP!"
            self.message_show = self.counter + 7
        elif self.score > 25000 and self.speed == 2:
            self.speed = 1
            self.message = "SPEED UP!"
            self.message_show = self.counter + 7

    def delete_lines(self):
        for i in self.current_coords:
            self.field[i[0]][i[1]] = 0
        lines = [all(i) for i in self.field]
        if not any(lines):
            for i in self.current_coords:
                self.field[i[0]][i[1]] = self.current_piece_color
            return False
        count = 0
        for i in range(18):
            if lines[i]:
                del self.field[i]
                count += 1
                self.field.insert(0, [0 for _ in range(10)])
        multiplier = 1
        if count == 1:
            self.score += 100 * multiplier
            self.message = f"+{100 * multiplier}"
            self.message_show = self.counter + 5
        elif count == 2:
            self.score += 300 * multiplier
            self.message = f"+{300 * multiplier}"
            self.message_show = self.counter + 5
        elif count == 3:
            self.score += 700 * multiplier
            self.message = f"+{700 * multiplier}"
            self.message_show = self.counter + 5
        elif count == 4:
            self.score += 1500 * multiplier
            self.message = f"TETRIS! +{1500 * multiplier}"
            self.message_show = self.counter + 7
        else:
            # print("More than 5 lines at a time error")
            self.score = 777777
        for i in self.current_coords:
            self.field[i[0]][i[1]] = self.current_piece_color
        return True


class TetrisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_records(self) -> str:
        records = list()
        for line in (
            open("databases/tetris_records.txt", encoding="utf-8")
            .read()
            .split("\n")
        ):
            if not line:
                continue
            records.append((int(line.split(" ")[1]), int(line.split(" ")[0])))
        records.sort(reverse=True)
        top_10 = ""
        count = 0
        for i in records:
            try:
                user = await self.bot.fetch_user(i[1])
                top_10 += f"{user.name}: {i[0]}\n"
                count += 1
            except Exception:
                continue
            if count >= 10:
                break
        return top_10

    @commands.slash_command(name="tetris", description="тетрис (сломан)")
    async def tetris(self, inter: disnake.ApplicationCommandInteraction):
        if len(active_games):
            await inter.response.send_message(
                "Игра уже где-то запущена. Пощадите рэйт лимит"
            )
            return
        message = await inter.channel.send(
            ":regional_indicator_t::regional_indicator_e:"
            ":regional_indicator_t::regional_indicator_r:"
            ":regional_indicator_i::regional_indicator_s:"
        )
        game = Tetris(message, inter.author)
        active_games[message.id] = game
        await game.update_image()
        await game.main_loop_v2()
        save(inter.author.id, int(game.score))
        await inter.channel.send(
            f"Игрок {inter.author.mention} набрал {int(game.score)}. Спасибо за игру!\n"
            f"```\nРекорды\n{await self.get_records()}\n```"
        )
        del active_games[message.id]
        # while not game.game_over:
        #     game.update_movement()
        #     if game.counter % game.speed == game.speed - 1:
        #         game.update_gravity()
        #         game.speedup()
        #     game.count()
        #     await game.update_image()
        #     if game.delete_lines():
        #         await game.update_image()
        # while not game.game_over:
        #     sleep(1)
        #     game.update_movement()
        #     await game.update_image()
        #     game.update_gravity()
        #     game.count()
        #     if game.delete_lines():
        #         await game.update_image()

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith(ID):
            return
        action = inter.component.custom_id[len(ID) :]
        if inter.message.id not in active_games:
            await inter.response.send_message(
                "Эта игра уже закончилась", ephemeral=True
            )
            return
        game = active_games[inter.message.id]
        if inter.author != game.player:
            await inter.response.send_message(
                "Это не ваша игра", ephemeral=True
            )
            return
        game.add_action(action)
        game.update_movement()
        try:
            await inter.response.send_message()
        except Exception:  # NOQA мне пофек, мне не нужно изменять сообщение
            pass
        # await inter.response.edit_message(str(game), components=game.components)


def setup(bot):
    bot.add_cog(TetrisCog(bot))
