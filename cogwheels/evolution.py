import asyncio
import colorsys
import time
from io import BytesIO
from random import randint

import disnake
import numpy as np
from disnake import ui
from disnake.ext import commands
from numpy import cos, pi, sin
from perlin_noise import PerlinNoise
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

ID = "evolution_"
BLUE = disnake.ButtonStyle.primary
GRAY = disnake.ButtonStyle.secondary
GREEN = disnake.ButtonStyle.success
RED = disnake.ButtonStyle.danger

players: dict[int:"Player"] = dict()


def normalize_matrix(matrix):
    min_val = matrix.min()
    range_val = np.ptp(matrix)  # peak-to-peak (max - min)
    normalized_matrix = (
        (matrix - min_val) / range_val
        if range_val != 0
        else np.zeros_like(matrix)
    )
    return normalized_matrix


def apply_color(pixel, color):
    r, g, b = color
    grayscale_value = pixel[0]
    alpha_value = pixel[3]
    return (
        int(grayscale_value * r / 255),
        int(grayscale_value * g / 255),
        int(grayscale_value * b / 255),
        alpha_value,
    )


def get_color(hue: float, saturation: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


class Being:
    def __init__(self, x: int, y: int, age_of_death: int, ancestor=None):
        self.health = 1
        self.age = 0
        self.x = x
        self.y = y
        self.age_of_death = age_of_death
        self.ancestor = ancestor

    def aging(self) -> None:
        self.age += 1
        if self.age > self.age_of_death:
            self.health = 0

    @staticmethod
    def is_moving():
        return False

    def is_alive(self) -> bool:
        return self.health > 0

    @staticmethod
    def get_image_deltas() -> tuple[int, int]:
        return 0, 0


class UnicellularAlgae(Being):
    def __init__(
        self,
        x: int,
        y: int,
        hue: float = 0.33,
        saturation: float = 0.5,
        average_age: float = 5,
        age_dispersion: float = 2.5,
        ancestor=None,
    ):
        self.color = get_color(hue, saturation)

        self.horizontal_flip = False
        self.vertical_flip = False

        age_of_death = max(
            1, round(np.random.normal(average_age, age_dispersion))
        )
        super().__init__(x, y, age_of_death, ancestor)

    def get_coordinates(self):
        return self.x, self.y

    def get_image(self, _):
        image = Image.open(
            "images/evolution_textures/pre-made/unicellular.png"
        ).convert("RGBA")
        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                pixels[x, y] = apply_color(pixels[x, y], self.color)
        if self.horizontal_flip:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if self.vertical_flip:
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        return image

    def take_energy(self, energy: float) -> None:
        pass

    def will_give_offspring(self) -> bool:
        pass

    def get_offspring_x_y(self) -> tuple[int, int]:
        pass

    def get_offspring(self):
        pass


class Algae:
    def __init__(self, x, y, ancestor=None):
        self.x = x
        self.y = y
        self.ancestor = ancestor

        self.hue = 0.5
        self.brightness = 0.5
        self.type = "одноклеточный"
        self.growth_stages = 0
        self.root_level = 0
        self.wide = False
        self.cancer = 0.01

        self.health = 1

        self.age = 0
        self.growth = 1

        self.horizontal_flip = False
        self.vertical_flip = False

    def get_image(self):
        path = "images/evolution_textures/pre-made/"
        if self.wide:
            image = Image.open(path + f"wide_{self.growth}")
        else:
            image = Image.open(path + f"thin_{self.growth}")
        return image

    def take_energy(self, energy: float):
        pass


class Player:
    def __init__(
        self,
        player_id: int,
        x: int,
        y: int,
        camera_direction: int,
    ):
        self.id = player_id
        self.game_message: disnake.Message | None = None
        self.x = x
        self.y = y
        self.camera_direction = camera_direction
        self.character_direction = 3
        self.last_update = 0

    def set_game_message(self, message: disnake.Message) -> None:
        self.game_message = message

    def set_coordinates(self, x: int, y: int) -> None:
        self.x, self.y = x, y

    def move(self, direction: int, size: tuple[int, int]) -> None:
        if direction == 0:
            self.x = (self.x + 1) % size[0]
        elif direction == 1:
            self.y = (self.y + 1) % size[1]
        elif direction == 2:
            self.x = (self.x - 1) % size[0]
        elif direction == 3:
            self.y = (self.y - 1) % size[1]
        self.character_direction = direction

    def get_coordinates(self) -> tuple[int, int]:
        return self.x, self.y

    def get_camera_direction(self) -> int:
        return self.camera_direction

    def rotate(self, delta: int) -> None:
        self.camera_direction = (self.camera_direction + delta) % 4

    def set_last_update(self) -> None:
        self.last_update = time.time()

    def get_image(self, direction: int) -> Image:
        direction = (self.character_direction - direction) % 4
        if direction == 2:
            return Image.open(
                "images/evolution_textures/character_right_down.png"
            )
        if direction == 3:
            return Image.open(
                "images/evolution_textures/character_left_down.png"
            )
        return Image.open("images/evolution_textures/character_no_face.png")

    @staticmethod
    def get_image_deltas():
        return 4, -22


class Planet:  # donut type
    def __init__(
        self,
        x: int,
        y: int,
        ticks_per_year: int,
        min_height: float = -20,
        max_height: float = 20,
    ):
        self.x = x
        self.y = y

        self.ticks_per_year = ticks_per_year
        self.tick_time = 1 / ticks_per_year

        self.min_height = min_height
        self.max_height = max_height
        self.height_range = max_height - min_height

        self.steps = 0
        self.time = 0
        self.tick_await = 1
        self.update_interval = 10
        self.last_update = 0
        self.slow_speed = True
        self.loop_started = False

        # self.seeds = [577453, 377886, 251466, 14000]
        # [338613, 536974, 476300, 429019] - хороший мир вода 45%
        # [897575, 331681, 540617, 420929] вода 45% мало земли на экваторе
        # [777640, 535970, 901265, 17393] 72% воды выглядит очень красиво, мало земли на экваторе, много островов
        # [517251, 302985, 719629, 297990] 51% воды, много островов
        self.seeds = []
        self.octaves = []

        self.height_map = None
        self.moisture_map = None
        self.color_map = None
        self.energy_map = None
        self.life_map: list[list[list]] = [
            [[] for _ in range(x)] for _ in range(y)
        ]
        self.life_tree = dict()
        self.life = set()

        start_time = time.time()
        self.generate()
        self.generate_energy_map()
        # self.generate_moisture_map()
        print(
            f"Evolution: генерация заняла {round((time.time() - start_time), 3)} секунд."
        )

        self.id = (
            "-".join([str(i) for i in self.seeds])
            + "_"
            + "-".join([str(i) for i in self.octaves])
        )
        self.generate_map_picture()
        # plt.imshow(self.moisture_map)
        # plt.show()

    def is_loop_started(self) -> bool:
        return self.loop_started

    def tick(self) -> None:
        self.steps += 1
        self.time += self.tick_time
        for life in self.life:
            x, y = life.get_coordinates()
            life.aging()
            if not life.is_alive():
                self.remove_from_life_map(life, x, y)
                del life
                continue
            if life.is_moving():
                pass
            life.take_energy(
                self.energy_map[self.steps % self.ticks_per_year][x][y]
            )

    async def tick_loop(self):
        while True:
            self.tick()
            if self.slow_speed:
                await asyncio.sleep(self.tick_await)
                if time.time() - self.last_update > self.update_interval:
                    try:
                        for player_id in players:
                            await self.update_image(player_id)
                    except Exception as e:
                        print("Evolution error:", e)
                    self.last_update = time.time()

    async def update_image(self, player_id: int):
        player = players[player_id]
        if player.game_message is None:
            return
        player.game_message.attachments = []
        if time.time() - player.last_update > 2:
            try:
                await player.game_message.edit(
                    self.get_text(player.id), file=planet.get_image(player.id)
                )
                player.set_last_update()
            except Exception as error:
                print("Evolution update_image() error: ", error)

    def get_size(self) -> tuple[int, int]:
        return self.x, self.y

    def get_time_of_year(self, y) -> str:
        planet_time = (self.time - 0.25) % 1
        if y < self.y / 2:
            planet_time = (planet_time - 0.5) % 1
        if planet_time <= 0.25:
            return "осень"
        if planet_time <= 0.5:
            return "зима"
        if planet_time <= 0.75:
            return "весна"
        return "лето"

    @staticmethod
    def get_components() -> list[disnake.ActionRow]:
        buttons = [
            ui.Button(emoji="↖️", custom_id=ID + "left_up", style=BLUE),
            ui.Button(emoji="🗺️", custom_id=ID + "map", style=BLUE),
            ui.Button(emoji="↗️", custom_id=ID + "right_up", style=BLUE),
            ui.Button(emoji="↪️", custom_id=ID + "rotate_left", style=BLUE),
            ui.Button(emoji="🦠", custom_id=ID + "set_life", style=GREEN),
            ui.Button(emoji="↩️", custom_id=ID + "rotate_right", style=BLUE),
            ui.Button(emoji="↙️", custom_id=ID + "left_down", style=BLUE),
            ui.Button(emoji="❔", custom_id=ID + "info", style=GRAY),
            ui.Button(emoji="↘️", custom_id=ID + "right_down", style=BLUE),
        ]
        rows = [3, 3, 3]
        components = [
            ui.ActionRow(*buttons[: sum(rows[:1])]),
            ui.ActionRow(*buttons[sum(rows[:1]) : sum(rows[:2])]),
            ui.ActionRow(*buttons[sum(rows[:2]) :]),
        ]
        return components

    def get_image(self, player_id) -> disnake.File:
        player = players[player_id]
        x, y = player.get_coordinates()
        direction = player.get_camera_direction()

        radius = 7
        start_z = self.height_map[y][x] - radius
        coords = self.calculate_coords_to_draw(x, y, direction, radius)

        to_place = []

        for line in coords:
            row = []
            for coord in line:
                place_count = self.height_map[coord[1]][coord[0]] - start_z + 1
                place_count = max(place_count, 0)
                is_water = self.height_map[coord[1]][coord[0]] <= 0
                lifeforms = self.life_map[coord[1]][coord[0]]
                row.append((is_water, place_count, lifeforms))
            to_place.append(row)

        image = Image.new("RGB", (960, 960), color=(174, 203, 214))
        start_x, start_y = 416, 432
        ground = Image.open("images/evolution_textures/ground64.png", "r")
        water = Image.open("images/evolution_textures/water64.png", "r")

        delta_x = 32
        delta_y = 16
        delta_z = 15

        count_x = 0
        for line in to_place:
            pic_x, pic_y = start_x, start_y
            count_y = 0
            for is_water, blocks, lifeforms in line:
                pic_x += delta_x
                pic_y += delta_y
                if is_water:
                    block = water
                else:
                    block = ground
                i = 0
                for i in range(blocks):
                    image.paste(block, (pic_x, pic_y - i * delta_z), block)
                for life in lifeforms:
                    life: UnicellularAlgae | Player
                    life_image = life.get_image(direction)
                    life_x, life_y = life.get_image_deltas()
                    image.paste(
                        life_image,
                        (pic_x + life_x, pic_y + life_y - i * delta_z),
                        life_image,
                    )
                count_y += 1
            count_x += 1
            start_x -= delta_x
            start_y += delta_y

        image.save(f"generated_images/evolution/interfaces/{player_id}.png")

        return disnake.File(
            f"generated_images/evolution/interfaces/{player_id}.png"
        )

    def get_text(self, player_id) -> str:
        player = players[player_id]
        x, y = player.get_coordinates()

        output = (
            f"### Планета Donurth\n"
            f"Итерация {self.steps}\nX: {x}, Y: {y}, Z: {self.height_map[y][x]}\n"
            f"Год {round(self.time + 1)}, {self.get_time_of_year(y)}\n"
            f"Температура: {round(self.energy_map[self.steps % self.ticks_per_year][y][x] * 0.8 - 40, 1)}"
        )
        return output

    def calculate_coords_to_draw(
        self, start_x: int, start_y: int, direction: int, radius: int
    ) -> list[list[tuple[int, int]]]:
        output = []

        if direction == 0:
            for y in range(start_y + radius, start_y - radius - 1, -1):
                row = []
                for x in range(start_x + radius, start_x - radius - 1, -1):
                    row.append((x % self.x, y % self.y))
                output.append(row)
        elif direction == 1:
            for x in range(start_x - radius, start_x + radius + 1):
                row = []
                for y in range(start_y + radius, start_y - radius - 1, -1):
                    row.append((x % self.x, y % self.y))
                output.append(row)
        elif direction == 2:
            for y in range(start_y - radius, start_y + radius + 1):
                row = []
                for x in range(start_x - radius, start_x + radius + 1):
                    row.append((x % self.x, y % self.y))
                output.append(row)
        elif direction == 3:
            for x in range(start_x + radius, start_x - radius - 1, -1):
                row = []
                for y in range(start_y - radius, start_y + radius + 1):
                    row.append((x % self.x, y % self.y))
                output.append(row)

        return output

    # def calculate_height_k(self, x: int, y: int) -> float:
    #     return e ** -(1.5 * (self.height_map[y][x] / self.max_height) ** 2)

    def calculate_height_k(self, x: int, y: int) -> float:
        return cos(self.height_map[y][x] / self.max_height * pi / 2)

    def generate(self) -> None:
        x, y = self.x, self.y
        self.octaves = [3, 10, 20, 45]
        if not self.seeds:
            self.seeds = [
                randint(0, 999),
                randint(0, 999),
                randint(0, 999),
                randint(0, 999),
            ]
        print("Сид:", self.seeds)
        noise1 = PerlinNoise(octaves=self.octaves[0], seed=self.seeds[0])
        noise2 = PerlinNoise(octaves=self.octaves[1], seed=self.seeds[1])
        noise3 = PerlinNoise(octaves=self.octaves[2], seed=self.seeds[2])
        noise4 = PerlinNoise(octaves=self.octaves[3], seed=self.seeds[3])
        noise = []
        for i in range(y):
            row = []
            for j in range(x):
                noise_val = noise1([j / x, i / y], tile_sizes=[1, 1])
                noise_val += 0.5 * noise2([j / x, i / y], tile_sizes=[1, 1])
                noise_val += 0.25 * noise3([j / x, i / y], tile_sizes=[1, 1])
                noise_val += 0.125 * noise4([j / x, i / y], tile_sizes=[1, 1])

                row.append(noise_val)
            noise.append(row)
        noise = np.array(noise)
        noise = (noise - np.min(noise)) / (np.max(noise) - np.min(noise))

        self.height_map = np.array(
            [
                [round(j * self.height_range + self.min_height) for j in i]
                for i in noise
            ]
        )
        self.height_map = np.where(
            self.height_map < 0, 0, self.height_map
        )  # без отрицательных

    def generate_moisture_map(self) -> None:
        underwater_mask = self.height_map <= 0
        distance_to_water = distance_transform_edt(~underwater_mask)
        moisture_map = np.zeros(self.y * self.x * self.ticks_per_year).reshape(
            self.y, self.x, self.ticks_per_year
        )
        self.moisture_map = normalize_matrix(moisture_map)

    def generate_energy_map(self) -> None:
        sun_power = 100
        season_amplitude = 1 / 40

        time_axis = np.linspace(0, 1, num=self.ticks_per_year, endpoint=False)
        output = np.zeros(self.y * self.x * self.ticks_per_year).reshape(
            self.y, self.x, self.ticks_per_year
        )
        for y in range(self.y):
            row = abs(
                sin(
                    (sin(2 * pi * time_axis) * season_amplitude + y / self.y)
                    * pi
                )
            )
            for x in range(self.x):
                output[y][x] = row * sun_power * self.calculate_height_k(x, y)
        self.energy_map = output.transpose(2, 0, 1)

    def generate_map_picture(self) -> None:
        water_count = 0
        x, y = self.x, self.y
        color_map = [[] for _ in range(y)]
        for i in range(len(self.height_map)):
            for j in self.height_map[i]:
                if j <= 0:
                    water_count += 1
                    color_map[i].append((120, 162, 204))
                else:
                    k = (j - self.min_height) / self.height_range
                    color_map[i].append(
                        (int(255 * k), int(255 * k), int(255 * k))
                    )
        print("Вода:", water_count / (x * y))

        img = Image.new(mode="RGB", size=(x, y))
        for i in range(y):
            for j in range(x):
                img.putpixel((j, i), color_map[i][j])
        # name = str(time.ctime()).replace(":", "_")
        img.save(f"generated_images/evolution/{self.id}.png")
        img.save("generated_images/evolution/most_recent.png")

    def move_player(self, player_id: int, direction: int):
        player = players[player_id]
        self.remove_from_life_map(player, player.x, player.y)
        player.move(direction, self.get_size())
        self.append_to_life_map(player, player.x, player.y)

    def set_player_coordinates(self, player: Player, x, y):
        self.remove_from_life_map(player, *player.get_coordinates())
        player.set_coordinates(x, y)
        self.append_to_life_map(player, x, y)

    def append_to_life_map(self, obj, x, y) -> None:
        self.life_map[y][x].append(obj)

    def insert_to_life_map(self, obj, x, y) -> None:
        self.life_map[y][x].insert(0, obj)

    def remove_from_life_map(self, obj, x, y) -> None:
        if obj in self.life_map[y][x]:
            self.life_map[y][x].remove(obj)

    def add_life(self, obj) -> None:
        self.life.add(obj)

    def get_height(self, x: int, y: int) -> int:
        return self.height_map[y][x]

    def get_life(self, x: int, y: int) -> list:
        return self.life_map[y][x]


planet: Planet | None = None


class EvolutionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ecosystem", description="тест")
    async def command(
        self,
        inter: disnake.ApplicationCommandInteraction,
        x: int = 0,
        y: int = 0,
        direction: int = 0,
    ):
        await inter.response.defer()

        global planet, players

        if planet is None:
            planet = Planet(200, 100, 1000)
        if inter.author.id in players:
            await players[inter.author.id].game_message.delete()
            player = players[inter.author.id]
            planet.set_player_coordinates(player, x, y)
        else:
            player = Player(
                inter.author.id, x % planet.x, y % planet.y, direction
            )
            planet.append_to_life_map(player, *player.get_coordinates())
            players[player.id] = player

        text = planet.get_text(inter.author.id)
        file = planet.get_image(inter.author.id)
        components = planet.get_components()

        message = await inter.followup.send(
            text, file=file, components=components
        )
        message = self.bot.get_message(message.id)
        player.set_game_message(message)

        if not planet.is_loop_started():
            _ = asyncio.create_task(planet.tick_loop())
            planet.loop_started = True

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith(ID):
            return
        action = inter.component.custom_id[len(ID) :]
        if inter.author != inter.message.interaction.author:
            await inter.response.send_message(
                "Это не ваше окно. Откройте новое с помощью /ecosystem.",
                ephemeral=True,
            )
            return
        if planet is None or inter.author.id not in players:
            await inter.response.send_message(
                "Это окно больше не работает. "
                "Откройте новое с помощью /ecosystem.",
                ephemeral=True,
            )
            return
        player = players[inter.author.id]
        direction = player.get_camera_direction()
        move_actions = ["left_up", "right_up", "right_down", "left_down"]

        # return после if, если не требуется обновление экрана
        if action == "map":
            x, y = player.get_coordinates()
            image = Image.open(f"generated_images/evolution/{planet.id}.png")
            draw = ImageDraw.Draw(image)
            draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill="red")

            bytes_io = BytesIO()
            image.save(bytes_io, format="PNG")
            bytes_io.seek(0)
            file = disnake.File(bytes_io, filename="map.png")
            await inter.response.send_message(
                "Ваше местоположение отмечено.", file=file, ephemeral=True
            )
            return
        if action == "info":
            await inter.response.send_message(
                "С помощью этой команды вы можете следить за симуляцией искусственной жизни на планете Donurth "
                "(donut + earth, т.к. планета на самом деле имеет форму тора).\n"
                "Кнопки движения двигают вас по карте. Чтобы телепортироваться на нужную точку, введите команду снова"
                " с нужными координатами.\n"
                "Кнопка карты показывает карту планеты и ваше местоположение на ней.\n"
                "Кнопка жизни зарождает самый первый организм в воде.\n"
                "\n⚠️На данный момент в разработке.⚠️",
                ephemeral=True,
            )
            return
        if action == "set_life":
            x, y = player.get_coordinates()
            height = planet.get_height(x, y)
            if height > 0:
                await inter.response.send_message(
                    "Вы не можете зародить новую жизнь на суше.", ephemeral=True
                )
                return
            if len(planet.get_life(x, y)) > 1:
                await inter.response.send_message(
                    "На этой клетке уже есть жизнь", ephemeral=True
                )
                return
            alga = UnicellularAlgae(x, y)
            planet.insert_to_life_map(alga, x, y)
            planet.add_life(alga)
        elif action in move_actions:
            direction = (direction + move_actions.index(action)) % 4
            planet.move_player(player.id, direction)
        elif action == "rotate_left":
            player.rotate(1)
        elif action == "rotate_right":
            player.rotate(-1)
        # Внутренности функции Planet.update_image, т.к. обязательно давать response
        inter.message.attachments = []
        await inter.response.edit_message(
            planet.get_text(player.id), file=planet.get_image(inter.author.id)
        )
        player.set_last_update()
        planet.tick()


def setup(bot):
    bot.add_cog(EvolutionCog(bot))


# ticks_per_year = 1000
# a = Planet(200, 100, ticks_per_year)
#
# fig = plt.figure()
# im = plt.imshow(a.energy_map[0], animated=True, cmap="plasma")
# plt.clim(0, 100)
#
# t = 0
#
# def updatefig(_):
#     global t
#     im.set_array(a.energy_map[t])
#     t = (t + 10) % ticks_per_year
#     return im,
#
# ani = animation.FuncAnimation(fig, updatefig, interval=1, blit=True)
# plt.show()


# todo
# исправить баг с не отображением
# сделать симуляцию водорослей
# сделать pickling
# сохранять древо эволюции
# возраст
