import asyncio
import disnake
import numpy as np
from disnake import ui
from disnake.ext import commands
from perlin_noise import PerlinNoise
from lloyd import Field
import math
import random
from main import GUILD_IDS

ID = "kuzoworld_"
game = False
choosing_emoji = set()

# points = np.random.rand(2000, 2)
# print(points)
# field = Field(points)
# for i in range(100):
#     field.relax()
# points = field.get_points()
# print(points)

# print("start")
# size = 100
# field = [[" " for _ in range(size)] for _ in range(size)]
# points = []
# coords = random.sample(range(size ** 2), 10)
# for y in range(size):
#     for x in range(size):
#         distances = []
#         for point in points:
#             delta_x = abs(point[0] - x)
#             delta_y = abs(point[1] - y)
#             if delta_x > size / 2:
#                 delta_x = size - delta_x
#             if delta_y > size / 2:
#                 delta_y = size - delta_y
#             result = math.hypot(delta_x, delta_y)
#             distances.append(result)
#         field[x][y] = str(distances.index(min(distances)) % 10)
# for i in field:
#     print("".join(i))


class Thing:
    def __init__(self, coords=None, emoji=None, collision=False, info=None, save_name=None):
        self.save_name = save_name
        self.coords = coords
        self.emoji = emoji
        self.collision = collision
        self.info = info

    def get_coords(self):
        return self.coords

    def set_coords(self, coords):
        self.coords = coords

    def has_emoji(self):
        if self.emoji:
            return True
        return False

    def get_emoji(self):
        return self.emoji

    def has_collision(self):
        return self.collision

    def set_info(self, info):
        self.info = info

    def has_info(self):
        if self.info:
            return True
        return False

    def get_info(self):
        return self.info


class Item:
    def __init__(self, name, emoji, damage=0):
        self.name = name
        self.emoji = emoji
        self.damage = damage


class Biome:
    def __init__(self, name, emoji, cells, spawn):
        self.name = name
        self.emoji = emoji
        self.cells = cells
        self.spawn = spawn

    def get_emoji(self):
        return self.emoji

    def get_name(self):
        return self.name

    def has_cell(self, coords):
        return coords in self.cells


class Player(Thing):
    def __init__(self, member: disnake.Member, emoji, coords):
        self.inventory = []
        self.updates = True
        self.member = member
        self.message = None
        super().__init__(coords=coords, emoji=emoji, collision=True, info=member.name, save_name="pl")

    def can_be_updated(self):
        return self.updates

    def turn_updates_on(self):
        self.updates = True

    def turn_updates_off(self):
        self.updates = False

    def get_save_name(self):
        return self.save_name

    def get_member(self):
        return self.member

    def get_message(self):
        return self.message

    def set_message(self, message):
        self.message = message

    def set_emoji(self, emoji):
        self.emoji = emoji

    async def del_message(self):
        await self.message.delete()
        self.message = None

    def has_message(self):
        if self.message:
            return True
        return False


class Planet:
    actions = {"left_up": (-1, -1), "up": (0, -1), "right_up": (1, -1),
               "left": (-1, 0), "right": (1, 0),
               "left_down": (-1, 1), "down": (0, 1), "right_down": (1, 1)}

    def __init__(self, bot, size, biomes, things):
        self.biomes = []
        self.size = int(size)
        self.all_players = dict()
        self.online_players = dict()
        self.field = [[[] for _ in range(self.size)] for _ in range(self.size)]
        for i in things.split("\n"):
            if not i:
                continue
            coords, thing = i.split("\t")
            coords, thing = coords.split(" "), thing.split("  ")
            x, y = int(coords[0]), int(coords[1])
            if thing[0] == "pl":  # pl  id  emoji  i n v e n t o r y
                member = bot.get_user(int(thing[1]))
                emoji = thing[2]
                coords = (x, y)
                self.all_players[member.id] = Player(member, emoji, coords)

    def __str__(self):
        output = str(self.size) + "\n\n"
        for i in self.biomes:
            output += f"{i.get_name()}"
        output += "\n\n"
        for i in self.field:
            for j in i:
                if not j:
                    continue
        return output

    def generate_biomes(self):
        cells = []
        for x in range(self.size):
            for y in range(self.size):
                cells.append((x, y))
        self.biomes = [Biome("mushroom_biome",
                             "🟩", cells,
                             [(Thing(emoji="🍄", collision=True), 0.05)])]
        for i in self.biomes:
            for j in i.spawn:
                number = int(self.size ** 2 * j[1])
                points = np.random.rand(number, 2)
                field = Field(points)
                for _ in range(50):
                    field.relax()
                new_points = field.get_points()
                for point in new_points:
                    x = int(point[0] * self.size)
                    y = int(point[1] * self.size)
                    if i.has_cell((x, y)) and j[0] not in self.field[y][x]:
                        j[0].set_coords((x, y))
                        self.field[y][x].append(j[0])

    def save(self):
        with open("databases/kuzoworld.txt", "w", encoding="utf-8") as file:
            file.write(str(self))

    def set_emoji(self, player_id, emoji):
        if player_id in self.online_players:
            self.online_players[player_id].set_emoji(emoji)
        else:
            print("КУЗОМИР: ОШИБКА СЭТА ЭМОДЗИ")

    def leave_player(self, player_id):
        self.online_players[player_id].set_message(None)
        x, y = self.online_players[player_id].get_coords()
        self.field[y][x].remove(self.online_players[player_id])
        del self.online_players[player_id]

    def unregister_player(self, player_id):
        self.online_players[player_id].set_message(None)
        x, y = self.online_players[player_id].get_coords()
        self.field[y][x].remove(self.online_players[player_id])
        del self.online_players[player_id]
        del self.all_players[player_id]

    def register_player(self, member, emoji):
        player = Player(member, emoji, (0, 0))
        self.field[0][0].append(player)
        self.online_players[member.id] = player
        self.all_players[member.id] = player

    def join_player(self, player_id):
        player = self.all_players[player_id]
        x, y = player.get_coords()
        self.field[y][x].append(player)
        self.online_players[player_id] = player

    def is_registered(self, player_id):
        if player_id in self.all_players:
            return True
        return False

    def can_join(self, player_id):
        if player_id in self.all_players and player_id not in self.online_players:
            return True
        return False

    def get_emoji(self, x, y):
        for i in self.field[y % self.size][x % self.size][::-1]:
            if i.has_emoji():
                return i.get_emoji()
        for i in self.biomes:
            if i.has_cell((x, y)):
                return i.get_emoji()
        return "⬛"

    def check_collision(self, x, y):
        for i in self.field[y % self.size][x % self.size]:
            if i.has_collision():
                return True
        return False

    def get_info(self, x, y):
        for i in self.field[y % self.size][x % self.size]:
            if i.has_info():
                return i.get_info()

    def get_image(self, player_id, radius=9):
        x, y = self.online_players[player_id].get_coords()
        output = f"X: {x} Y: {y}\n"
        output += "\n"  # сообщение
        deltas = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
        arrows = ["↖️", "⬆️", "↗️", "⬅️", "➡️", "↙️", "⬇️", "↘️"]
        for i in range(8):
            delta_x, delta_y = deltas[i]
            info = self.get_info(x + delta_x, y + delta_y)
            if info:
                output += f"({arrows[i]} {info}) "
        output += "\nВ руках: ничего.\n"
        left = radius // 2
        right = radius // 2 + 1
        for i in range(y - left, y + right):
            for j in range(x - left, x + right):
                output += self.get_emoji(j % self.size, i % self.size)
            output += '\n'
        return output

    def get_components(self, player_id):
        buttons = [ui.Button(emoji="↖️", custom_id=ID + "left_up", style=disnake.ButtonStyle.primary),
                   ui.Button(emoji="⬆️", custom_id=ID + "up", style=disnake.ButtonStyle.primary),
                   ui.Button(emoji="↗️", custom_id=ID + "right_up", style=disnake.ButtonStyle.primary),
                   ui.Button(emoji="⬅️", custom_id=ID + "left", style=disnake.ButtonStyle.primary),
                   ui.Button(emoji="⏺️", custom_id=ID + "mid", style=disnake.ButtonStyle.primary),
                   ui.Button(emoji="➡️", custom_id=ID + "right", style=disnake.ButtonStyle.primary),
                   ui.Button(emoji="↙️", custom_id=ID + "left_down", style=disnake.ButtonStyle.primary),
                   ui.Button(emoji="⬇️", custom_id=ID + "down", style=disnake.ButtonStyle.primary),
                   ui.Button(emoji="↘️", custom_id=ID + "right_down", style=disnake.ButtonStyle.primary)]
        x, y = self.online_players[player_id].get_coords()
        deltas = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
        for i in range(8):
            delta_x, delta_y = deltas[i]
            if i >= 4:
                i += 1
            if self.check_collision(x + delta_x, y + delta_y):
                buttons[i].disabled = True
        components = [ui.ActionRow(*buttons[:3]),
                      ui.ActionRow(*buttons[3:6]),
                      ui.ActionRow(*buttons[6:])]
        return components

    def move_player_by_action(self, player_id, action):
        coords = self.actions[action]
        self.move_player(player_id, coords)

    def move_player(self, player_id, coords):
        x, y = self.online_players[player_id].get_coords()
        delta_x, delta_y = coords
        if self.check_collision(x + delta_x, y + delta_y):
            return
        self.field[y][x].remove(self.online_players[player_id])
        self.field[(y + delta_y) % self.size][(x + delta_x) % self.size].append(self.online_players[player_id])
        self.online_players[player_id].set_coords(((x + delta_x) % self.size, (y + delta_y) % self.size))

    async def update_game_messages(self, player_id, self_update=False):
        x, y = self.online_players[player_id].get_coords()
        await self.update_game_messages_by_coords(x, y, self_update=self_update)

    async def update_game_messages_by_coords(self, x, y, self_update=False):
        players_to_update = set()
        for i in range(y - 5, y + 6):
            for j in range(x - 5, x + 6):
                if i == y and j == x and not self_update:
                    continue
                cell = self.field[i % self.size][j % self.size]
                for thing in cell:
                    if isinstance(thing, Player):
                        players_to_update.add(thing)
        for i in players_to_update:
            if not i.can_be_updated():
                continue
            await i.get_message().edit(self.get_image(i.get_member().id),
                                       components=self.get_components(i.get_member().id))

    async def send_game_message(self, inter: disnake.ApplicationCommandInteraction):
        if self.online_players[inter.author.id].has_message():
            await self.online_players[inter.author.id].message.delete()
        game_message = await inter.channel.send(self.get_image(inter.author.id),
                                                components=self.get_components(inter.author.id))
        self.online_players[inter.author.id].set_message(game_message)

    def get_message(self, player_id):
        if player_id in self.online_players:
            return self.online_players[player_id].get_message()

    def get_coords(self, player_id):
        return self.online_players[player_id].get_coords()

    def get_online_players(self):
        return self.online_players

    async def do_action(self, player_id, action):
        player_x, player_y = self.online_players[player_id].get_coords()
        delta_x, delta_y = self.actions[action]
        x, y = player_x + delta_x, player_y + delta_y
        if not self.check_collision(x, y):
            self.move_player(player_id, (delta_x, delta_y))


class KuzoworldCog(commands.Cog):
    allowed_emojis = ('😀😃😄😁😆😅🤣😂🙂🙃🫠😉😊😇🥰😍🤩😘😗☺️😚😙🥲😋😛😜🤪😝🤑🤗🤭🫢🫣🤫🤔🫡🤐🤨😐😑😶🫥😶‍🌫️😏😒'
                      '🙄😬😮‍💨🤥🫨😌😔😪🤤😴😷🤒🤕🤧🥴😵😵‍💫🤯🤠🥳🥸😎🤓🧐😕🫤😟🙁☹️😮😯😲😳🥺🥹😦😧😨'
                      '😰😥😢😭😱😖😣😞😓😩😫🥱😤😠😡🤬😈👿')

    def __init__(self, bot):
        self.bot = bot

    async def kuzoworld(self, inter: disnake.ApplicationCommandInteraction):
        global game
        await inter.response.send_message('...', delete_after=0)
        data = open("databases/kuzoworld.txt", "r", encoding="utf-8").read()
        print(data)
        print(data.split("\n\n"))
        size, biomes, things = data.split("\n\n")
        if not game:
            game = Planet(self.bot, size, biomes, things)
            game.generate_biomes()
        if inter.author.id in choosing_emoji:
            await inter.response.send("Отправьте свой эмодзи")
            return
        if game.can_join(inter.author.id):
            game.join_player(inter.author.id)
        elif not game.is_registered(inter.author.id):
            choosing_emoji.add(inter.author.id)
            await inter.followup.send("Отправьте свой эмодзи")
            try:
                while True:
                    message = await self.bot.wait_for("message", timeout=120)
                    if message.author != inter.author:
                        continue
                    emoji = message.content.strip()
                    if emoji in self.allowed_emojis:
                        break
                    await inter.followup.send("Этот эмодзи нельзя использовать. "
                                              "Пожалуйста, выберите самые простые эмодзи"
                                              " из первой вкладки \"Люди\".", ephemeral=True)
                game.register_player(inter.author, emoji)
                choosing_emoji.remove(inter.author.id)
            except asyncio.TimeoutError:
                await inter.followup.send(f"Время ожидания истекло", ephemeral=True)
                choosing_emoji.remove(inter.author.id)
                return
        await game.send_game_message(inter)
        await game.update_game_messages(inter.author.id)
        game.save()

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if ID not in inter.component.custom_id:
            return

        global game
        if not game:
            await inter.response.send_message("Игра сейчас закрыта. "
                                              "Вы можете открыть её через /кузомир .", ephemeral=True)
            return
        elif not game.get_message(inter.author.id) or inter.message.id != game.get_message(inter.author.id).id:
            await inter.response.send_message("Вы не играете в этом окне. "
                                              "Вы можете открыть ваше окно через /кузомир ", ephemeral=True)
            return
        elif inter.author.id in choosing_emoji:
            await inter.response.send_message("Сначала выберите эмодзи.", ephemeral=True)
            return
        else:
            action = inter.component.custom_id[len(ID):]
        if action == "mid":
            x, y = game.get_coords(inter.author.id)
            await inter.response.edit_message(f"X: {x} Y: {y}\n"
                                              f"Игроков онлайн: {len(game.get_online_players())}", components=[
                ui.Button(label="Вернуться", custom_id=ID + "main_screen", style=disnake.ButtonStyle.secondary),
                ui.Button(label="Выйти из игры", custom_id=ID + "leave", style=disnake.ButtonStyle.primary),
                ui.Button(label="Поменять эмодзи", custom_id=ID + "change_emoji", style=disnake.ButtonStyle.primary),
                ui.Button(label="Удалить персонажа", custom_id=ID + "delete_ask", style=disnake.ButtonStyle.danger)
            ])
            return
        elif action == "main_screen":
            await inter.response.edit_message(game.get_image(inter.author.id),
                                              components=game.get_components(inter.author.id))
            game.online_players[inter.author.id].turn_updates_on()
            return
        elif action == "leave":
            await inter.response.edit_message("Закрываю...", components=[])
            await game.online_players[inter.author.id].get_message().delete()
            x, y = game.get_coords(inter.author.id)
            game.leave_player(inter.author.id)
            await game.update_game_messages_by_coords(x, y)
            return
        elif action == "change_emoji":
            await inter.response.send_message("Отправьте свой эмодзи", ephemeral=True)
            choosing_emoji.add(inter.author.id)
            try:
                while True:
                    message = await self.bot.wait_for("message", timeout=120)
                    if message.author != inter.author:
                        continue
                    emoji = message.content.strip()[0]
                    if emoji in self.allowed_emojis:
                        break
                    await inter.followup.send("Этот эмодзи нельзя использовать. "
                                              "Пожалуйста, выберите самые простые эмодзи"
                                              " из первой вкладки \"Люди\".", ephemeral=True)
                game.set_emoji(inter.author.id, emoji)
                await game.update_game_messages(inter.author.id, self_update=True)
                game.online_players[inter.author.id].turn_updates_on()
                try:
                    if isinstance(inter.channel, disnake.TextChannel):
                        await message.delete()
                except Exception as error:
                    await inter.channel.send("(У бота недостаточно прав для удаления сообщений)")
                    print(error)
                response = await inter.original_response()
                await response.delete()
                game.save()
            except asyncio.TimeoutError:
                await inter.followup.send(f"Время ожидания истекло", ephemeral=True)
            choosing_emoji.remove(inter.author.id)
            return
        elif action == "delete_ask":
            await inter.response.edit_message("Вы уверены, что хотите удалить персонажа?", components=[
                ui.Button(label="Назад", custom_id=ID + "mid", style=disnake.ButtonStyle.secondary),
                ui.Button(label="Да", custom_id=ID + "delete", style=disnake.ButtonStyle.danger)])
            return
        elif action == "delete":
            await inter.response.edit_message("Удаляю...")
            await game.online_players[inter.author.id].get_message().delete()
            game.unregister_player(inter.author.id)
            game.save()
            return
        await game.do_action(inter.author.id, action)
        await inter.response.edit_message(game.get_image(inter.author.id),
                                          components=game.get_components(inter.author.id))
        await game.update_game_messages(inter.author.id)
        game.save()


def setup(bot):
    bot.add_cog(KuzoworldCog(bot))
