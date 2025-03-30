import asyncio
import math
import random
import time

import disnake
import numpy
import roman
from disnake import ui
from disnake.ext import commands
from lloyd import Field
from perlin_noise import PerlinNoise
from PIL import Image

ID = "kuzoworld_"
INVISIBLE = "ㅤ"
BLUE = disnake.ButtonStyle.primary
GRAY = disnake.ButtonStyle.secondary
GREEN = disnake.ButtonStyle.success
RED = disnake.ButtonStyle.danger

choosing_item = dict()
choosing_emoji = set()
generated_stars = dict()
game = None


def generate_star(star_type=None):
    star = Star()
    star.generate(star_type=star_type)
    return star


async def game_loop(a_game):
    while True:
        await a_game.on_tick()
        await asyncio.sleep(1)


class Structure:
    def __init__(
        self,
        name=None,
        emoji=None,
        statistics=None,
        coords=None,
        showed_info=None,
        collision=False,
        actions_on_use=None,
        actions_on_near=None,
        actions_on_collision=None,
        actions_on_attack=None,
        movable=False,
        use_items=None,
        drop=None,
        capacity=0,
        inside_items=None,
        showed_name=None,
    ):
        self.name = name
        self.showed_name = showed_name
        self.coords = coords
        self.emoji = emoji
        if statistics is None:
            statistics = dict()
        self.statistics = statistics
        self.collision = collision
        if actions_on_use is None:
            actions_on_use = dict()
        self.actions_on_use = actions_on_use
        if actions_on_near is None:
            actions_on_near = dict()
        self.actions_on_near = actions_on_near
        if actions_on_collision is None:
            actions_on_collision = dict()
        self.actions_on_collision = actions_on_collision
        if actions_on_attack is None:
            actions_on_attack = dict()
        self.actions_on_attack = actions_on_attack
        self.movable = movable
        self.showed_info = showed_info
        if use_items is None:
            use_items = list()
        self.use_items = use_items
        if drop is None:
            drop = list()
        self.drop = drop
        self.capacity = capacity
        if inside_items is None:
            inside_items = list()
        self.inside_items = inside_items

    def get_copy(self):
        drop = []
        for i in self.drop:
            drop.append(i.get_copy())
        inside_items = []
        for i in self.inside_items:
            inside_items.append(i.get_copy())
        return Structure(
            self.name,
            self.emoji,
            self.statistics.copy(),
            self.coords,
            self.showed_info,
            self.collision,
            self.actions_on_use.copy(),
            self.actions_on_near.copy(),
            self.actions_on_collision.copy(),
            self.actions_on_attack.copy(),
            self.movable,
            self.use_items.copy(),
            drop,
            self.capacity,
            inside_items,
            self.showed_name,
        )

    def set_actions_on_use(self, actions):
        self.actions_on_use = actions

    def set_use_items(self, items):
        self.use_items = items

    def get_inside_items(self):
        return self.inside_items

    def get_drop(self):
        return self.drop

    def get_capacity(self):
        return self.capacity

    def get_showed_name(self):
        return self.showed_name

    def get_showed_info(self):
        return self.showed_info

    def set_showed_info(self, s):
        self.showed_info = s

    def get_statistic(self, key):
        return self.statistics[key]

    def get_statistics(self):
        return self.statistics

    def change_statistic(self, stat_name, delta):
        self.statistics[stat_name] += delta

    def set_emoji(self, emoji):
        self.emoji = emoji

    def get_emoji(self):
        return self.emoji

    def is_usable(self, player):
        if self.use_items:
            return player.get_main_item() in self.use_items
        return bool(self.actions_on_use)

    def get_actions_on_use(self):
        return self.actions_on_use

    def get_actions_on_near(self):
        return self.actions_on_near

    def get_actions_on_collision(self):
        return self.actions_on_collision

    def get_coords(self):
        return self.coords

    def set_coords(self, coords):
        self.coords = coords

    def get_collision(self):
        return self.collision

    def get_name(self):
        return self.member.name


class Player(Structure):
    def __init__(
        self,
        member,
        emoji,
        game_message=None,
        statistics=None,
        inventory=None,
        star_name=None,
        planet_number=None,
        planet_level=None,
        coords=None,
        first_landed=False,
        ship=None,
        always_show=None,
        limited_show=None,
        never_show=None,
        dead=False,
    ):
        self.dead = dead
        self.updating = False
        self.member = member
        self.game_message = game_message
        if inventory is None:
            inventory = Inventory()
        self.inventory = inventory
        self.main_item = None
        self.star_name = star_name
        self.planet_number = planet_number
        self.planet_level = planet_level
        self.updates = True
        self.first_landed = first_landed
        self.ship = ship
        self.mode = "use_mode"
        if statistics is None:
            statistics = {"health": 100, "hunger": 100, "oxygen": 100}
        if always_show is None:
            always_show = ["health", "hunger"]
        self.always_show = always_show
        if limited_show is None:
            limited_show = [("oxygen", 100)]
        self.limited_show = limited_show
        if never_show is None:
            never_show = list()
        self.never_show = never_show
        super().__init__(
            name="player",
            emoji=emoji,
            coords=coords,
            collision=True,
            statistics=statistics,
            showed_info=self.member.name,
        )

    def set_main_item(self, item):
        self.main_item = item

    def check_death(self):
        if self.statistics["health"] <= 0:
            self.statistics["health"] = 0
            return True
        return False

    def is_dead(self):
        return self.dead

    def set_dead(self, dead):
        self.dead = dead

    def become_dead(self):
        self.__init__(self.member, self.emoji, self.game_message, dead=True)

    def tick_update(self):
        self.change_statistic("hunger", -0.17)
        if self.statistics["hunger"] <= 0:
            self.change_statistic("health", -2)
            self.statistics["hunger"] = 0

    def set_updating_status(self, status):
        self.updating = status

    def is_updating(self):
        return self.updating

    def get_inventory(self):
        return self.inventory

    def get_always_show(self):
        return self.always_show

    def get_limited_show(self):
        return self.limited_show

    def get_main_item(self):
        return self.main_item

    def have_landed_before(self):
        return self.first_landed

    def set_first_landed(self, first_landed):
        self.first_landed = first_landed

    def get_planet_number(self):
        return self.planet_number

    def set_planet_number(self, number):
        self.planet_number = number

    def set_planet_level(self, level):
        self.planet_level = level

    def turn_updates_off(self):
        self.updates = False

    def turn_updates_on(self):
        self.updates = True

    def can_be_updated(self):
        return self.updates

    def is_on_planet(self):
        return bool(self.coords)

    def get_id(self):
        return self.member.id

    def get_location(self):
        return self.star_name, self.planet_number, self.planet_level

    def get_star_name(self):
        return self.star_name

    def get_game_message(self):
        return self.game_message

    def get_ship(self):
        return self.ship

    async def delete_game_message(self):
        if self.game_message:
            try:
                await self.game_message.delete()
                self.game_message = None
            except Exception as error:  # если не найдено сообщение
                print(error)
                self.game_message = None

    def set_game_message(self, message):
        self.game_message = message

    def set_star_name(self, star_name):
        self.star_name = star_name

    def set_mode(self, mode):
        self.mode = mode

    def get_mode(self):
        return self.mode

    def set_inventory(self, inv):
        self.inventory = inv


class Biome:
    def __init__(
        self,
        name,
        emoji,
        number_of_points=0,
        level=-1.0,
        direction=None,
        companion=None,
        companion_distance=None,
        cells=None,
        noise=10,
        special=None,
        spawns=None,
        certain_spawns=None,
        collision=False,
    ):
        self.name = name
        self.emoji = emoji
        self.level = level  # не использовать левелы, сплошной позор
        self.number = number_of_points
        self.spawns = spawns
        self.certain_spawns = certain_spawns
        self.noise = noise
        self.special = special
        self.direction = direction
        if cells is None:
            cells = []
        self.cells = cells
        self.companion = companion
        self.companion_distance = companion_distance
        self.collision = collision

    def get_spawns(self):
        return self.spawns

    def get_collision(self):
        return self.collision

    def get_companion(self):
        return self.companion

    def get_emoji(self):
        return self.emoji

    def get_companion_distance(self):
        return self.companion_distance

    def get_level(self):
        return self.level

    def get_direction(self):
        return self.direction

    def get_noise(self):
        return self.noise

    def get_number_of_points(self):
        return self.number

    def is_special(self):
        return bool(self.special)

    def is_leveled(self):
        return self.level != -1

    def get_name(self):
        return self.name

    def get_cells(self):
        return self.cells

    def add_cell(self, coords):
        self.cells.append(coords)

    def remove_cell(self, coords):
        self.cells.remove(coords)

    def has_cell(self, coords):
        return coords in self.cells


class World:
    def __init__(
        self,
        planet_type=None,
        moon=None,
        size=None,
        biomes=None,
        fields=None,
        roman_numeral=None,
        generated_levels=None,
        conditions=None,
    ):
        self.generating_right_now = False
        self.moon = moon
        self.size = size
        if fields is None:
            fields = dict()
        self.fields = fields
        if biomes is None:
            biomes = list()
        self.biomes = biomes
        self.type = planet_type
        self.online_players = []
        self.roman_numeral = roman_numeral
        if generated_levels is None:
            generated_levels = list()
        self.generated_levels = generated_levels
        self.conditions = conditions

    def land_player(self, player: Player):
        while self.generating_right_now:
            time.sleep(3)
        self.online_players.append(player.get_id())
        coords = None
        coords_not_chosen = True
        spawn_biomes = ["mushroom_forest"]
        radius = 3
        while coords_not_chosen:
            coords = (
                random.randint(
                    round(self.size / 2 - radius), round(self.size / 2 + radius)
                ),
                random.randint(
                    round(self.size / 2 - radius), round(self.size / 2 + radius)
                ),
            )
            if not self.get_cell_collision(coords, 0):
                for i in self.biomes[0]:
                    if i in spawn_biomes and self.biomes[0][i].has_cell(coords):
                        coords_not_chosen = False
                        break
            if radius < self.size / 2 - 2:
                radius += 0.2
        if player.have_landed_before():
            self.fields[0][coords[0]][coords[1]] = [player.get_ship(), player]
        else:
            self.fields[0][coords[0]][coords[1]] = [player]
        player.set_coords(coords)

    def get_cell(self, coords, level):
        return self.fields[level][coords[0]][coords[1]]

    def get_cell_emoji(self, coords, level):
        y, x = coords
        for i in self.fields[level][y][x]:
            emoji = i.get_emoji()
            if emoji:
                return emoji
        for i in self.biomes[level]:
            biome = self.biomes[level][i]
            if biome.has_cell(coords):
                return biome.get_emoji()
        print("Кузомир ошибка: клетка не принадлежит ни одному биому")

    def get_image(self, coords, level, radius=4):
        y, x = coords
        output = ""
        for i in range(y - radius, y + radius + 1):
            for j in range(x - radius, x + radius + 1):
                output += self.get_cell_emoji(
                    (i % self.size, j % self.size), level
                )
            output += "\n"
        return output

    def set_roman(self, number):
        self.roman_numeral = number

    def get_roman(self):
        return self.roman_numeral

    def get_cell_collision(self, coords, level):
        for i in self.get_cell(coords, level):
            if i.get_collision():
                return True
        for i in self.biomes[level]:
            biome = self.biomes[level][i]
            if biome.has_cell(coords) and biome.get_collision():
                return True
        return False

    def get_field(self, number):
        return self.fields[number]

    def get_emoji(self):
        emojis = {"spawn": "🪐", "empty": "🌑"}
        return emojis[self.type]

    def generate(
        self, star_type, moon=False, world_type=None, custom_probabilities=None
    ):
        self.moon = moon
        if world_type:
            self.type = world_type
        elif custom_probabilities:
            self.type = numpy.random.choice(*custom_probabilities)[0]
        else:
            self.type = numpy.random.choice(["empty"], 1, p=[1])[0]
        if self.type == "spawn":  # первичная генерация
            self.size = random.randint(125, 150)
            self.conditions = 2
            self.biomes = [
                {
                    "sea": Biome(
                        "sea",
                        "🟦",  # 🟦🍉
                        10,
                        noise=15,
                        companion="beach",
                        companion_distance=5,
                        collision=True,
                    ),
                    "desert": Biome(
                        "desert",
                        "🟨",
                        3,
                        noise=10,
                        spawns=[(THINGS["cactus"], 0.01)],
                    ),
                    "dense_desert": Biome(
                        "dense_desert",
                        "🟨",
                        2,
                        noise=15,
                        spawns=[(THINGS["cactus"], 0.2)],
                        companion="desert",
                        companion_distance=30,
                    ),
                    "denser_forest": Biome(
                        "denser_forest",
                        "🟩",
                        5,
                        spawns=[
                            (THINGS["tree"], 0.1),
                            (THINGS["mushroom"], 0.03),
                        ],
                        noise=10,
                        companion="mushroom_forest",
                        companion_distance=10,
                    ),
                    "mushroom_forest": Biome(
                        "mushroom_forest",
                        "🟩",
                        25,
                        spawns=[
                            (THINGS["tree"], 0.02),
                            (THINGS["mushroom"], 0.04),
                        ],
                        noise=20,
                    ),
                    "beach": Biome("beach", "🟨"),
                }
            ]
        elif self.type == "empty":
            self.conditions = 0
            self.size = random.randint(70, 150)

    def generate_points_with_relaxation(self, number, iterations):
        points = numpy.random.rand(number, 2)
        if len(points) > 3:
            field = Field(points)
            for _ in range(iterations):
                field.relax()
            points = [
                (round(i[0] * self.size), round(i[1] * self.size))
                for i in field.get_points()
            ]
        else:
            points = [
                (round(i[0] * self.size), round(i[1] * self.size))
                for i in points
            ]
        number = len(points)
        points = set(points)
        while number != len(points):
            points.add(
                (
                    int(random.random() * self.size),
                    int(random.random() * self.size),
                )
            )
        return list(points)

    def generate_level(self, level):
        self.generating_right_now = True
        self.generated_levels.append(level)
        noise_y_seed = random.randint(1, 10**9)
        noise_x_seed = random.randint(1, 10**9)
        start_time = time.time()
        generated_cells = self.generate_leveled_biomes(level)
        biomes = dict()
        for key in self.biomes[level]:
            if not self.biomes[level][key].is_leveled():
                biomes[key] = self.biomes[level][key]
        number = sum([biomes[i].get_number_of_points() for i in biomes])
        points = self.generate_points_with_relaxation(number, 64)
        biomes_points = dict()
        for i in biomes:
            number = biomes[i].get_number_of_points()
            name = biomes[i].get_name()
            for j in range(number):
                if name in biomes_points:
                    biomes_points[name].append(points.pop())
                else:
                    biomes_points[name] = [points.pop()]
        noise = PerlinNoise(octaves=self.size // 10, seed=noise_x_seed)
        noise_y = [
            [noise([i / self.size, j / self.size]) for j in range(self.size)]
            for i in range(self.size)
        ]
        noise = PerlinNoise(octaves=self.size // 10, seed=noise_y_seed)
        noise_x = [
            [noise([i / self.size, j / self.size]) for j in range(self.size)]
            for i in range(self.size)
        ]

        for old_y in range(self.size):
            for old_x in range(self.size):
                if (old_y, old_x) in generated_cells:
                    continue
                companions = []
                distances = []
                for biome in biomes_points:
                    points = biomes_points[biome]
                    y = int(
                        old_y
                        + noise_y[old_y][old_x] * biomes[biome].get_noise()
                    )
                    x = int(
                        old_x
                        + noise_x[old_y][old_x] * biomes[biome].get_noise()
                    )
                    biome_distances = []
                    for point in points:
                        delta_y = abs(point[0] - y)
                        delta_x = abs(point[1] - x)
                        if delta_y > self.size // 2:
                            delta_y = self.size - delta_y
                        if delta_x > self.size // 2:
                            delta_x = self.size - delta_x
                        result = math.hypot(delta_y, delta_x)
                        biome_distances.append(result)
                    result = (min(biome_distances), biome)
                    distances.append(result)
                    companion = biomes[biome].get_companion()
                    if companion:
                        companions.append((biome, companion, result[0]))
                distance, biome = min(distances)
                companion = biomes[biome].get_companion()
                priorities = {"spawn": "dense_desert"}
                if not companion or biome == priorities[self.type]:
                    for i in companions:
                        if i[0] != biome and (
                            i[2] - biomes[i[0]].get_companion_distance()
                            < distance
                        ):
                            biome = i[1]
                            break
                biomes[biome].add_cell((old_y, old_x))

        self.fields[level] = [
            [[] for _ in range(self.size)] for _ in range(self.size)
        ]
        for i in biomes:
            biome = biomes[i]
            spawns = biome.get_spawns()
            if spawns is None:
                continue
            for j in spawns:
                number = round(self.size**2 * j[1])
                points = self.generate_points_with_relaxation(number, 15)
                for point in points:
                    if self.get_biome_of_a_cell(point, level) == biome:
                        cell = self.fields[level][point[0]][point[1]]
                        cell.append(j[0].get_copy())
        self.generating_right_now = False

        print(
            f"Генерация завершена. Размер: {self.size}, Сид Y: {noise_y_seed}, Сид X: {noise_x_seed}, "
            f"Точки: {biomes_points}"
        )
        colors = {
            "desert": (255, 255, 0),
            "mushroom_forest": (0, 255, 0),
            "empty": (0, 0, 0),
            "sea": (0, 0, 255),
            "mountains": (255, 255, 255),
            "dense_desert": (255, 127, 0),
            "beach": (255, 255, 128),
            "denser_forest": (0, 200, 0),
        }
        print(round((time.time() - start_time), 2), "секунд.")
        img = Image.new(mode="RGB", size=(self.size, self.size))
        for i in self.biomes[level]:
            for j in self.biomes[level][i].cells:
                img.putpixel(j, colors[i])
        img = img.rotate(angle=270)
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        name = str(time.ctime()).replace(":", "_").replace(" ", "")
        img.save("generated_images/" + name + ".png")

    def get_biome_of_a_cell(self, coords, level):
        for i in self.biomes[level]:
            biome = self.biomes[level][i]
            if biome.has_cell(coords):
                return biome

    def generate_leveled_biomes(self, level):
        biomes = self.biomes[level]
        noise = PerlinNoise(octaves=10, seed=random.randint(1, 10**6))
        noise = [
            [noise([i / self.size, j / self.size]) for j in range(self.size)]
            for i in range(self.size)
        ]
        generated_cells = []
        leveled_biomes = []
        for i in biomes:
            if biomes[i].is_leveled():
                leveled_biomes.append(biomes[i])
        for biome in leveled_biomes:
            if biome.get_direction() == 1:

                def func(a, b):
                    return a > b
            else:

                def func(a, b):
                    return a < b

            biome_level = biome.get_level()
            for y in range(self.size):
                for x in range(self.size):
                    if func(noise[y][x], biome_level):
                        generated_cells.append((y, x))
                        biome.add_cell((y, x))
        return generated_cells

    def is_generated(self, level):
        return level in self.generated_levels

    def get_type_name(self):
        type_names = {
            "spawn": "Планета-приют",
        }
        return type_names[self.type]

    def get_type(self):
        return self.type

    def get_conditions(self):
        conditions = {
            -2: "Враждебные",
            -1: "Неблагоприятные",
            0: "Приемлемые",
            1: "Обнадёживающие",
            2: "Благоприятные",
        }
        return conditions[self.conditions]

    def get_size(self):
        return self.size

    def is_moon(self):
        return self.moon

    def get_online_players(self):
        return self.online_players

    def get_online_players_number(self):
        return len(self.online_players)

    def add_online_player(self, player_id):
        if player_id not in self.online_players:
            self.online_players.append(player_id)

    def remove_online_player(self, player_id):
        if player_id in self.online_players:
            self.online_players.remove(player_id)


class Star:
    def __init__(self, name=None, star_type=None, planets=None):
        self.name = name
        self.type = star_type
        if planets is None:
            planets = list()
        self.planets = planets  # list of Worlds
        self.online_players = []
        self.all_players = []

    def generate_name(self):
        self.name = (
            random.choice("DFGJLNQRSUVWYZ")
            + "-"
            + str(random.randint(0, 9))
            + str(random.randint(0, 9))
        )

    def get_components(self):
        buttons = [
            ui.Button(
                label="Улететь", style=BLUE, custom_id=ID + "deep_space_ask"
            )
        ]
        for i in range(len(self.planets)):
            label = f"{self.name} {self.planets[i].get_roman()}"
            buttons.append(
                ui.Button(
                    label=label,
                    style=GRAY,
                    custom_id=ID + "open_planet_" + str(i),
                )
            )
        components = [[buttons[0]]]
        temp = []
        for i in range(1, len(buttons)):
            temp.append(buttons[i])
            if i % 5 == 0:
                components.append(temp)
                temp = []
        if temp:
            components.append(temp)
        for i in range(len(components)):
            components[i] = ui.ActionRow(*components[i])
        components.append(components[0])
        del components[0]
        return components

    def add_player(self, player_id):
        if player_id not in self.all_players:
            self.all_players.append(player_id)
        if player_id not in self.online_players:
            self.online_players.append(player_id)

    def remove_online_player(self, player_id):
        self.online_players.remove(player_id)

    def remove_player(self, player_id):
        self.online_players.remove(player_id)
        self.all_players.remove(player_id)

    def generate(self, star_type=None, custom_probabilities=None):
        self.generate_name()
        if star_type:
            self.type = star_type
        elif custom_probabilities:
            self.type = numpy.random.choice(*custom_probabilities)[0]
        else:
            # ядовитая, скалистая, живая, мёртвая, пустынная, чёрная дыра, туманность
            self.type = numpy.random.choice(
                [
                    "normal",
                    "big",
                    "double",
                    "empty",
                    "fairy",
                ],
                1,
                p=[0.21, 0.21, 0.31, 0.17, 0.10],
            )[0]
        number_of_planets = 0
        number_of_moons = 0

        if self.type == "spawn":
            number_of_planets = random.randint(1, 2)
            if number_of_planets:
                number_of_moons = random.randint(0, 1)
        elif self.type == "normal":
            number_of_planets = random.randint(1, 3)
            if number_of_planets:
                number_of_moons = random.randint(0, 1)
        elif self.type == "big":
            number_of_planets = random.randint(1, 2)
            if number_of_planets:
                number_of_moons = random.randint(0, 4)
        elif self.type == "double":
            number_of_planets = random.randint(2, 3)
            if number_of_planets:
                number_of_moons = random.randint(0, 1)
        elif self.type == "empty":
            number_of_planets = random.randint(0, 2)
            number_of_moons = random.randint(0, 0)

        for i in range(number_of_planets):
            planet = World()
            planet.generate(self.type)
            self.planets.append(planet)
        for i in range(number_of_moons):
            moon = World()
            moon.generate(self.type, moon=True)
            self.planets.insert(random.randint(1, len(self.planets)), moon)

        if self.type == "spawn":
            planet = World()
            planet.generate(self.type, world_type="spawn")
            self.planets.insert(random.randint(0, len(self.planets)), planet)
        elif self.type == "fairy":
            pass  # вомп вомп

        moon_number = 0
        moon_counter = 0
        for i in range(len(self.planets)):
            planet = self.planets[i]
            if planet.is_moon():
                moon_number += 1
                moon_counter += 1
                planet.set_roman(
                    f"{roman.toRoman(i - moon_number + 1)}-{roman.toRoman(moon_counter)}"
                )
            else:
                moon_counter = 0
                planet.set_roman(f"{roman.toRoman(i - moon_number + 1)}")

    def get_planets(self):
        return self.planets

    def get_planet(self, number):
        return self.planets[number]

    def get_name(self):
        return self.name

    def get_type(self):
        return self.type

    def get_type_name(self):
        type_names = {
            "spawn": "Звезда-приют",
            "normal": "Умеренная звезда",
            "double": "Звёзды-близнецы",
            "big": "Звезда-обитель",
            "empty": "Пустотная звезда",
            "fairy": "Сказочная звезда",
        }
        return type_names[self.type]

    def get_emoji(self):
        emojis = {
            "spawn": "☀️",
            "normal": "☀️",
            "double": "☀️☀️",
            "big": "🌞",
            "empty": "🔆",
            "fairy": "🌟",
        }
        return emojis[self.type]

    def get_online_players(self):
        return self.online_players

    def get_online_players_number(self):
        return len(self.online_players)

    def get_all_players(self):
        return self.all_players

    def get_all_players_number(self):
        return len(self.all_players)


class Game:
    def __init__(self, bot, stars=None, star_limit=2, all_players=None):
        self.message = None
        self.ticks = 0
        self.bot = bot
        self.star_limit = star_limit
        if stars is None:
            stars = dict()
        self.stars = stars  # name: Star
        if all_players is None:
            all_players = dict()
        self.all_players = all_players  # player_id: Player
        self.online_players = dict()  # player_id: Player

    async def tick_loop(self):
        while True:
            await self.on_tick()  # Call the on_tick method
            await asyncio.sleep(1)  # Wait for 1 second

    async def on_tick(self):
        self.ticks += 1
        players = self.get_players_on_planet()
        for player in players:
            if not player.is_dead():
                player.tick_update()
            if player.check_death():
                await self.on_death(player)
        if self.ticks % 10 == 0:
            start_time = time.time()
            await self.update_players_on_tick()
            # print("Кузомир кадр:", round((time.time() - start_time), 2))

    async def on_death(self, player):
        player_id = player.get_id()
        if player.is_dead():
            return
        player.set_dead(True)
        player.turn_updates_off()
        field = self.get_field_by_player(player.get_id())
        y, x = player.get_coords()
        inventory = player.get_inventory()
        inside_items = inventory.get_items()
        bag = inventory.get_bag()
        if bag:
            inside_items.append(bag)
        field[y][x].append(
            Structure(
                name="coffin",
                emoji="⚰️",
                showed_info=f"Гроб {player.get_name()}",
                showed_name=f"Гроб {player.get_name()}",
                inside_items=inside_items,
                capacity=0,
                collision=True,
                actions_on_use={"open_container": None},
            )
        )
        field[y][x].remove(player)
        star_name, planet_number, level = player.get_location()
        star = self.get_star(star_name)
        planet = star.get_planet(planet_number)
        image = planet.get_image((y, x), level, radius=2)
        components = [
            ui.Button(
                label="Начать заново", style=BLUE, custom_id=ID + "reset"
            ),
            ui.Button(
                label="Выйти", style=RED, custom_id=ID + "delete_game_message"
            ),
        ]
        await player.get_game_message().edit(image, components=components)
        await self.update_by_player(player_id)
        star.remove_player(player_id)
        planet.remove_online_player(player_id)
        if star.get_all_players_number() == 0:
            del self.stars[star.get_name()]
            await self.update_cosmos(None, True, player_id)
        else:
            await self.update_cosmos(star_name, True, player_id)
        del self.online_players[player_id]

    def send_message(self, message, sleep_time):
        self.message = message
        time.sleep(sleep_time)
        self.message = None

    def get_possible_items(self, player_id, structure=None):
        player = self.get_player(player_id)
        inventory = player.get_inventory()
        bag = inventory.get_bag()
        items1 = inventory.get_items()
        if bag:
            items1.append(bag)
        items2 = []
        if structure:
            items2 = structure.get_inside_items()
        elif bag:
            items2 = bag.get_inside_items()
        return items1, items2

    def get_inventory_image(self, player_id, structure=None):
        items1, items2 = self.get_possible_items(player_id, structure)
        player = self.get_player(player_id)
        bag = player.get_inventory().get_bag()
        main_item = player.get_main_item()
        output = f"{player.get_emoji()} {player.get_name()}\n\n"
        counter = 0
        for item in items1:
            counter += 1
            if item == main_item:
                output += "➡️\t"
            else:
                output += f"{counter}\t"
            if item == bag and not structure:
                output += (
                    f"{item.get_emoji()} {item.get_showed_name()} содержит:\n"
                )
            else:
                output += f"{item.get_emoji()} {item.get_showed_name()} - {item.get_quantity()}\n"
        if structure:
            output += f"{structure.get_emoji()} {structure.get_showed_name()} содержит:\n"
        if (bag or structure) and not items2:
            output += "\tПусто\n"
        for item in items2:
            counter += 1
            if item == main_item:
                output += "\t➡️\t"
            else:
                output += f"\t{counter}\t"
            output += f"{item.get_emoji()} {item.get_showed_name()} - {item.get_quantity()}\n"
        if main_item:
            desc = main_item.get_description()
            if desc:
                output += f"\n{main_item.get_description()}\n"
        output += "\nВведите цифру, чтобы выбрать нужный предмет."
        return output

    def get_inventory_components(self, player_id, structure=None):
        buttons = [
            ui.Button(label="Вернуться", style=GRAY, custom_id=ID + "update"),
            ui.Button(
                label="Переложить",
                style=BLUE,
                custom_id=ID + "move_item_one",
                disabled=True,
            ),
            ui.Button(
                label="Переложить всё",
                style=BLUE,
                custom_id=ID + "move_item",
                disabled=True,
            ),
            ui.Button(
                label="Разделить",
                style=BLUE,
                custom_id=ID + "split_item",
                disabled=True,
            ),
            ui.Button(
                label="Сложить",
                style=BLUE,
                custom_id=ID + "merge_item",
                disabled=True,
            ),
            ui.Button(
                label="Использовать",
                style=GREEN,
                custom_id=ID + "use_item",
                disabled=True,
            ),
            ui.Button(
                label="Выбросить",
                style=RED,
                custom_id=ID + "drop_item_one",
                disabled=True,
            ),
            ui.Button(
                label="Выбросить всё",
                style=RED,
                custom_id=ID + "drop_item",
                disabled=True,
            ),
        ]
        items1, items2 = self.get_possible_items(player_id, structure)
        player = self.get_player(player_id)
        main_item = player.get_main_item()
        inventory = player.get_inventory()
        bag = inventory.get_bag()
        if structure:
            chest = structure
        elif bag:
            chest = bag
        else:
            chest = None
        if not main_item:
            return buttons
        print("chest", chest)
        print(items1, items2)
        for item in items1:
            if (
                item.get_name() == main_item.get_name()
                and item.get_quantity() < item.get_stack()
                and item != main_item
                and main_item in items1
            ):
                buttons[4].disabled = False
            if (
                item.get_name() == main_item.get_name()
                and item.get_quantity() < item.get_stack()
                and main_item in items2
            ) or len(items2) < chest.get_capacity():
                buttons[1].disabled = False
                buttons[2].disabled = False
            if item == main_item:
                if (
                    len(items1) < inventory.get_capacity()
                    and item.get_quantity() != 1
                ):
                    buttons[3].disabled = False
                if item.is_usable(player):
                    buttons[5].disabled = False
                buttons[-2].disabled = False
                if item.get_quantity() > 1:
                    buttons[-1].disabled = False
        for item in items2:
            if (
                item.get_name() == main_item.get_name()
                and item.get_quantity() < item.get_stack()
                and item != main_item
                and main_item in items2
            ):
                buttons[4].disabled = False
            if (
                item.get_name() == main_item.get_name()
                and item.get_quantity() < item.get_stack()
                and main_item in items2
            ) or len(items1) < inventory.get_capacity():
                buttons[1].disabled = True
            if item == main_item:
                if (
                    len(items1) < inventory.get_capacity()
                    and item.get_quantity() != 1
                ):
                    buttons[3].disabled = False
                if item.is_usable(player):
                    buttons[5].disabled = False
                buttons[-2].disabled = False
                if item.get_quantity() > 1:
                    buttons[-1].disabled = False
        return buttons

    async def update_inventory_message(self, player_id, structure):
        player = self.get_player(player_id)
        message = player.get_game_message()
        image, components = (
            self.get_inventory_image(player_id, structure),
            self.get_inventory_components(player_id, structure),
        )
        await message.edit(image, components=components)

    async def open_inventory(
        self, player_id, structure=None, update_message=False
    ):
        global choosing_item
        if update_message:
            await self.update_inventory_message(player_id, structure)
        choosing_item[player_id] = structure

    async def inventory_loop(self):
        while True:
            message = await self.bot.wait_for("message")
            player_id = message.author.id
            if player_id not in self.online_players:
                continue
            if player_id not in choosing_item:
                continue

            number = message.content.strip()
            structure = choosing_item[player_id]

            try:
                number = int(number) - 1
            except ValueError:
                continue
            if isinstance(message.channel, disnake.TextChannel):
                try:
                    await message.delete()
                except PermissionError as error:
                    print(error)

            items1, items2 = self.get_possible_items(player_id, structure)
            all_items = items1 + items2

            if not (0 <= number < len(all_items)):
                self.get_player(player_id).set_main_item(None)
            else:
                self.get_player(player_id).set_main_item(all_items[number])
            await self.update_inventory_message(player_id, structure)

    def get_deep_space_image(self):
        output = f"Доступно звёзд: {len(self.stars)}\n\n"
        for player in self.get_players_without_a_star():
            output += f"[{player.get_emoji()}] {player.get_name()}\n"
        output += "\n"
        for star_name in self.stars:
            star = self.get_star(star_name)
            player_number = star.get_online_players_number()
            output += f"{star.get_emoji()} {star.get_name()}. {star.get_type_name()}. Игроков: {player_number}\n\n"
        return output

    def get_star_menu_image(self, player_id):
        star_name = self.get_player(player_id).get_star_name()
        star = self.get_star(star_name)
        planets = star.get_planets()
        output = f"{star.get_emoji()} {star_name}. {star.get_type_name()}\n\n"
        for player in self.get_players_of_a_star(star_name):
            if player.get_planet_number() is None:
                output += f"[{player.get_emoji()}] {player.get_name()}\n"
        output += "\n"
        for planet in planets:
            if planet.is_moon():
                output += (
                    INVISIBLE
                    + f"  ⤷ {planet.get_emoji()} {star_name} {planet.get_roman()}"
                )
            else:
                output += (
                    f"- {planet.get_emoji()} {star_name} {planet.get_roman()}"
                )
            if planet.get_type() == "spawn":
                output += f". {planet.get_type_name()}"
            online = planet.get_online_players_number()
            if online:
                output += f"\t\tИгроков: {online}"
            output += "\n"
        return output

    def get_image(self, player_id):
        star, planet, level = self.get_location(player_id)
        if star is None:
            return self.get_deep_space_image()
        if planet is None:
            return self.get_star_menu_image(player_id)
        planet = self.get_star(star).get_planet(planet)
        stat_names = {"health": "❤️‍", "hunger": "🍽️", "oxygen": "O₂"}
        player = self.get_player(player_id)
        output = player.get_name() + "\n"
        main_item = player.get_main_item()
        if main_item:
            output += f"В руках: {main_item.get_emoji()} {main_item.get_showed_name()}\n"
        else:
            output += "В руках: ничего\n"
        stats = player.get_statistics()
        for stat in player.get_always_show():
            output += f"{stat_names[stat]}: {round(stats[stat])}  "
        for i in player.get_limited_show():
            if stats[i[0]] != i[1]:
                output += f"{stat_names[i[0]]}: {round(stats[i[0]])}  "
        output += "\n"  # место для информации вокруг
        deltas = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]
        arrows = ["↖️", "⬆️", "↗️", "⬅️", "➡️", "↙️", "⬇️", "↘️"]
        field = self.get_field_by_player(player_id)
        size = planet.get_size()
        y, x = player.get_coords()
        for i in range(8):
            for j in field[(y + deltas[i][0]) % size][
                (x + deltas[i][1]) % size
            ]:
                info = j.get_showed_info()
                if info:
                    output += f"({arrows[i]} {info})  "
        output += "\n"
        if self.message:
            output += self.message + "\n"
        output += planet.get_image(self.get_coords(player_id), level)
        y = size // 2 - y
        x = x - planet.get_size() // 2
        output += f"X: {x}, Y: {y}"
        return output

    async def make_game_message(self, player_id, do_actions=True):
        components = await self.get_components(player_id, do_actions)
        image = self.get_image(player_id)
        return image, components

    async def get_components(self, player_id, do_actions=True):
        buttons = []
        star_name, planet_number, level = self.get_location(player_id)
        if star_name is None:
            disabled = self.is_star_limit_reached()
            buttons.append(
                ui.Button(
                    label="Отправиться к новой",
                    style=BLUE,
                    custom_id=ID + "generate_star",
                    disabled=disabled,
                )
            )
            for i in self.stars:
                buttons.append(
                    ui.Button(
                        label=self.stars[i].get_name(),
                        style=GRAY,
                        custom_id=ID
                        + f"go_to_a_star_{self.stars[i].get_name()}",
                    )
                )
            components = [[buttons[0]]]
            temp = []
            for i in range(1, len(buttons)):
                temp.append(buttons[i])
                if i % 5 == 0:
                    components.append(temp)
                    temp = []
            if temp:
                components.append(temp)
            for i in range(len(components)):
                components[i] = ui.ActionRow(*components[i])
            components.append(components[0])
            del components[0]
            return components
        if planet_number is None:
            star = self.get_star(star_name)
            return star.get_components()
        player = self.get_player(player_id)
        y, x = player.get_coords()
        field = self.get_field_by_player(player_id)
        buttons = [
            ui.Button(emoji="↖️", custom_id=ID + "left_up", style=BLUE),
            ui.Button(emoji="⬆️", custom_id=ID + "up", style=BLUE),
            ui.Button(emoji="↗️", custom_id=ID + "right_up", style=BLUE),
            ui.Button(
                emoji="👆", custom_id=ID + "use_mode", style=BLUE, disabled=True
            ),
            ui.Button(emoji="⬅️", custom_id=ID + "left", style=BLUE),
            ui.Button(emoji="⏺️", custom_id=ID + "mid", style=BLUE),
            ui.Button(emoji="➡️", custom_id=ID + "right", style=BLUE),
            ui.Button(
                emoji="🏗️",
                custom_id=ID + "build_mode",
                style=BLUE,
                disabled=True,
            ),
            ui.Button(emoji="↙️", custom_id=ID + "left_down", style=BLUE),
            ui.Button(emoji="⬇️", custom_id=ID + "down", style=BLUE),
            ui.Button(emoji="↘️", custom_id=ID + "right_down", style=BLUE),
            ui.Button(
                emoji="⚔️",
                custom_id=ID + "attack_mode",
                style=BLUE,
                disabled=True,
            ),
            ui.Button(
                emoji="💼",
                custom_id=ID + "inventory",
                style=BLUE,
                disabled=True,
            ),
            ui.Button(
                emoji="🛠️", custom_id=ID + "craft", style=BLUE, disabled=True
            ),
            ui.Button(emoji="⚫", custom_id=ID + "use_item", disabled=True),
        ]
        main_item = player.get_main_item()
        if main_item and main_item.is_usable(player):
            buttons[-1].emoji = main_item.get_emoji()
            buttons[-1].disabled = False
            buttons[-1].style = GREEN
        for i in buttons:
            if i.custom_id[len(ID) :] == player.get_mode():
                i.disabled = True
                i.style = GREEN
        deltas = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]
        choose_button = [0, 1, 2, 4, 6, 8, 9, 10]
        planet = self.get_star(star_name).get_planet(planet_number)
        size = planet.get_size()
        if do_actions:
            for i in field[y][x]:
                await self.do_actions(
                    i.get_actions_on_collision(), player_id, (y, x)
                )
            for i in range(8):
                for j in field[(y + deltas[i][0]) % size][
                    (x + deltas[i][1]) % size
                ]:
                    await self.do_actions(
                        j.get_actions_on_near(), player_id, (y, x)
                    )
        for i in range(8):
            coords = ((y + deltas[i][0]) % size, (x + deltas[i][1]) % size)
            cell = field[coords[0]][coords[1]]
            if (
                self.get_star(star_name)
                .get_planet(planet_number)
                .get_cell_collision(coords, level)
            ):
                buttons[choose_button[i]].disabled = True
            for j in cell:
                if j.is_usable(player):
                    buttons[choose_button[i]].style = GREEN
                    buttons[choose_button[i]].disabled = False
        components = [
            ui.ActionRow(*buttons[0:4]),
            ui.ActionRow(*buttons[4:8]),
            ui.ActionRow(*buttons[8:12]),
            ui.ActionRow(*buttons[12:]),
        ]
        return components

    async def do_player_action(self, action, player_id):
        player = self.get_player(player_id)
        star_name, planet_number, level = player.get_location()
        planet = self.get_star(star_name).get_planet(planet_number)
        field = self.get_field_by_location(star_name, planet_number, level)
        size = planet.get_size()
        y, x = player.get_coords()
        main_item = player.get_main_item()
        if action == "use_item":
            await self.do_actions(main_item.get_actions_on_use(), player_id)
            return
        if action == "move_item":
            structure = choosing_item[player_id]
            bag = player.get_inventory().get_bag()
            main_item = player.get_main_item()
            if bag == main_item:
                return
            if structure:
                chest = structure
            elif bag:
                chest = bag
            else:
                return
            items1 = player.get_inventory().get_items()
            items2 = chest.get_inside_items()
            if main_item in items1:
                items = items2
            else:
                items = items1
            for item in items:
                if (
                    item.get_name() == main_item.get_name()
                    and item.get_quantity() < item.get_stack()
                ):
                    quantity = main_item.get_quantity()
                    can_be_put = item.get_stack() - item.get_quantity()
                    if quantity <= can_be_put:
                        item.change_quantity(quantity)
                        main_item.change_quantity(-quantity)
                    else:
                        item.set_quantity(item.get_stack())
                        main_item.change_quantity(-can_be_put)
                    if main_item.get_quantity() == 0:
                        items = player.get_inventory().get_items()
                        bag = player.get_inventory().get_bag()
                        if main_item in items:
                            items.remove(main_item)
                        elif bag and main_item in bag.get_items():
                            bag_items.remove(main_item)
                        else:
                            structure.get_inside_items().remove(main_item)
                        break
            print("Кузомир ошибка: предмет для сдвига не найден")
            return
        if action == "split_item":
            structure = choosing_item[player_id]
            inventory = player.get_inventory()
            items1, items2 = self.get_possible_items(player_id, structure)
            main_item = player.get_main_item()
            for item in items1:
                if (
                    item == main_item
                    and len(items1) < inventory.get_capacity()
                    and item.get_quantity() != 1
                ):
                    quantity = main_item.get_quantity()
                    left, new = quantity // 2, quantity // 2 + quantity % 2
                    main_item.set_quantity(left)
                    new_item = main_item.get_copy()
                    new_item.set_quantity(new)
                    items1.append(new_item)
                    return
            for item in items2:
                if (
                    item == main_item
                    and len(items2) < inventory.get_capacity()
                    and item.get_quantity() != 1
                ):
                    quantity = main_item.get_quantity()
                    left, new = quantity // 2, quantity // 2 + quantity % 2
                    main_item.set_quantity(left)
                    new_item = main_item.get_copy()
                    new_item.set_quantity(new)
                    items2.append(new_item)
                    return
        elif action == "merge_item":
            structure = choosing_item[player_id]
            items1, items2 = self.get_possible_items(player_id, structure)
            main_item = player.get_main_item()
            for item in items1:
                if (
                    item.get_name() == main_item.get_name()
                    and item.get_quantity() < item.get_stack()
                    and item != main_item
                    and main_item in items1
                ):
                    quantity = main_item.get_quantity()
                    can_be_put = item.get_stack() - item.get_quantity()
                    if quantity <= can_be_put:
                        item.change_quantity(quantity)
                        main_item.change_quantity(-quantity)
                    else:
                        item.set_quantity(item.get_stack())
                        main_item.change_quantity(-can_be_put)
                    if main_item.get_quantity() == 0:
                        items = player.get_inventory().get_items()
                        items.remove(main_item)
            for item in items2:
                if (
                    item.get_name() == main_item.get_name()
                    and item.get_quantity() < item.get_stack()
                    and item != main_item
                    and main_item in items2
                ):
                    quantity = main_item.get_quantity()
                    can_be_put = item.get_stack() - item.get_quantity()
                    if quantity <= can_be_put:
                        item.change_quantity(quantity)
                        main_item.change_quantity(-quantity)
                    else:
                        item.set_quantity(item.get_stack())
                        main_item.change_quantity(-can_be_put)
                    if main_item.get_quantity() == 0:
                        bag = player.get_inventory().get_bag()
                        if bag and main_item in bag.get_items():
                            bag_items.remove(main_item)
                        else:
                            structure.get_inside_items().remove(main_item)
                        break
            return
        elif action == "drop_item_one":
            self.drop_item(player_id, quantity=1)
            return
        elif action == "drop_item":
            self.drop_item(player_id)
            return
        # move-actions
        deltas = {
            "left_up": (-1, -1),
            "up": (-1, 0),
            "right_up": (-1, 1),
            "left": (0, -1),
            "right": (0, 1),
            "left_down": (1, -1),
            "down": (1, 0),
            "right_down": (1, 1),
        }
        delta_y, delta_x = deltas[action]
        new_y, new_x = (y + delta_y) % size, (x + delta_x) % size
        cell = field[new_y][new_x]
        for i in cell:
            if i.is_usable(player):
                await self.do_actions(
                    i.get_actions_on_use(), player_id, (new_y, new_x)
                )
                return
        if planet.get_cell_collision((new_y, new_x), level):
            return
        field[y][x].remove(player)
        field[new_y][new_x].append(player)
        player.set_coords((new_y, new_x))

    def drop_item(self, player_id, item=None, quantity=None):
        player = self.get_player(player_id)
        field = self.get_field_by_player(player_id)
        y, x = player.get_coords()
        if item is None:
            item = player.get_main_item()
        if quantity is None:
            quantity = item.get_quantity()
        player.get_inventory().change_quantity(item, -quantity)
        dropped_item = item.get_copy()
        if item.get_quantity() == 0:
            player.set_main_item(None)
        dropped_item.set_quantity(quantity)
        for i in field[y][x]:
            if i.get_name() == "dropped_items":
                i.get_actions_on_use()["pick_up"].append(0, dropped_item)
                return
        field[y][x].append(
            Structure(
                name="dropped_items",
                emoji="📦",
                coords=(y, x),
                showed_info=f"Вещи {player.get_name()}",
                collision=False,
                actions_on_use={"pick_up": [dropped_item]},
            )
        )

    async def do_actions(self, actions, player_id, coords=None):
        global choosing_item
        player = self.get_player(player_id)
        cell = None
        structure = None
        main_item = player.get_main_item()
        for action in actions:
            if coords:
                field = self.get_field_by_player(player_id)
                cell = field[coords[0]][coords[1]]
                for i in cell:
                    if i.is_usable(player):
                        structure = i
                        break
            args = actions[action]

            if action == "change_player_statistics":
                statistics = player.get_statistics()
                for key, delta, max_value in args:
                    if key in statistics:
                        statistics[key] += delta
                        if statistics[key] > max_value:
                            statistics[key] = max_value
                        elif statistics[key] < 0:
                            statistics[key] = 0
                    else:
                        print(
                            "Кузомир Ошибка: Попытка изменить несуществующее значение"
                        )
            elif action == "pick_up":
                inventory = player.get_inventory()
                for item in args.copy():
                    leftover = inventory.put(item, player)
                    if leftover:
                        item.set_quantity(leftover)
                    else:
                        args.remove(item)
                if not args:
                    cell.remove(structure)
            elif action == "give":
                inventory = player.get_inventory()
                leftover = inventory.put(args, player)
                if leftover:
                    item = args.get_copy()
                    item.set_quantity(leftover)
                    self.drop_item(player_id, item)
            elif action == "change_quantity":
                items1 = player.get_inventory().get_items()
                structure = None
                if player_id in choosing_item:
                    structure = choosing_item[player_id]
                bag = player.get_inventory().get_bag()
                items2 = []
                if structure:
                    items2 = structure.get_inside_items()
                elif bag:
                    items2 = bag.get_inside_items()
                main_item.change_quantity(args)
                if main_item.get_quantity() == 0:
                    if main_item in items1:
                        items1.remove(main_item)
                    else:
                        items2.remove(main_item)
                    player.set_main_item(None)
            elif action == "open_container":
                player.turn_updates_off()
                choosing_item[player_id] = structure
            elif action == "replace":
                cell.remove(structure)
                if args:
                    cell.append(args)
            elif action == "change_showed_info":
                structure.set_showed_info(args)

    async def connect_player(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        player_id = inter.author.id
        global generated_stars

        if player_id in self.online_players:  # меняет окно
            await self.online_players[player_id].delete_game_message()
            if player_id in generated_stars:
                stars = generated_stars[player_id]
                output = "Вы можете полететь лишь на одну из трёх найденных звёзд. На какую вы полетите?\n\n"
                for star in stars:
                    output += f"{star.get_emoji()} {star.get_name()}. {star.get_type_name()}\n\n"
                buttons = []
                for i in range(len(stars)):
                    star = stars[i]
                    buttons.append(
                        ui.Button(
                            label=star.get_name(),
                            style=BLUE,
                            custom_id=ID + f"add_star_{i}",
                        )
                    )
                components = [ui.ActionRow(i) for i in buttons]
                generated_stars[player_id] = stars
                message = await inter.channel.send(
                    output, components=components
                )
                self.get_player(player_id).set_game_message(message)
                return
        elif (
            player_id in self.all_players
            and not self.get_player(player_id).is_dead()
        ):
            # присоединяет зарегистрированного игрока
            self.online_players[player_id] = self.get_player(player_id)
            y, x = self.get_coords(player_id)
            if self.is_on_planet(player_id):
                self.get_field_by_player(player_id)[y][x].append(
                    self.online_players[player_id]
                )
            star, planet, _ = self.get_player(player_id).get_location()
            if star:
                self.get_star(star).add_player(player_id)
            if planet:
                self.get_star(star).get_planet(planet).add_online_player(
                    player_id
                )
        else:  # регистрирует игрока
            emoji = await self.choose_emoji(inter)
            if not emoji:
                return
            self.all_players[player_id] = Player(inter.author, emoji)
            self.online_players[player_id] = self.get_player(player_id)
            image, components = await self.make_game_message(player_id)
            game_message = await inter.channel.send(
                image, components=components
            )
            self.get_player(player_id).set_game_message(game_message)
            await self.update_cosmos(None, True)
            print(f"Кузомир: Игрок {inter.author.name} зарегистрирован")
            return
        image, components = await self.make_game_message(player_id)
        game_message = await inter.channel.send(image, components=components)
        self.online_players[player_id].set_game_message(game_message)
        await self.update_on_join(player_id)

    async def update_on_join(self, player_id):
        if self.is_on_planet(player_id):
            await self.update_by_player(player_id)
        star_name = self.get_star_name_of_a_player(player_id)
        if star_name:
            await self.update_cosmos(star_name, True)
        else:
            await self.update_cosmos(None, True)

    async def update_cosmos(
        self, star_name, update_deep_space=False, player_id=None
    ):
        if update_deep_space:
            for player in self.get_players_without_a_star():
                if player.get_id() == player_id or not player.can_be_updated():
                    continue
                image, components = await self.make_game_message(
                    player.get_id()
                )
                if player.get_game_message():
                    await player.get_game_message().edit(
                        image, components=components
                    )
        if star_name in self.stars:
            players_to_update = []
            for player in self.get_players_of_a_star(star_name):
                if (
                    player.get_id() == player_id
                    or not player.can_be_updated()
                    or player.get_planet_number() is not None
                ):
                    continue
                player.set_updating_status(True)
                players_to_update.append(player)
            for player in players_to_update:
                image, components = await self.make_game_message(
                    player.get_id()
                )
                await player.get_game_message().edit(
                    image, components=components
                )
                player.set_updating_status(False)

    async def update_by_player(self, player_id, self_update=False):
        location = self.get_location(player_id)
        coords = self.get_coords(player_id)
        await self.update_by_location(location, coords, self_update=self_update)

    async def update_one_player(self, player_id):
        player = self.get_player(player_id)
        if player.can_be_updated():
            player.set_updating_status(True)
            image, components = await self.make_game_message(player.get_id())
            await player.get_game_message().edit(image, components=components)
            player.set_updating_status(False)

    async def update_by_location(self, location, coords, self_update=True):
        players = set()
        field = self.get_field_by_location(*location)
        y, x = coords
        for i in range(y - 5, y + 6):
            for j in range(x - 5, x + 6):
                if i == y and j == x and not self_update:
                    continue
                cell = field[i % len(field)][j % len(field)]
                for thing in cell:
                    if isinstance(thing, Player):
                        players.add(thing)
        players_to_update = set()
        for player in players:
            if not player.can_be_updated():
                continue
            player.set_updating_status(True)
            players_to_update.add(player)
        for player in players_to_update:
            image, components = await self.make_game_message(player.get_id())
            await player.get_game_message().edit(image, components=components)
            player.set_updating_status(False)

    async def update_players_on_tick(self):
        players_to_update = set()
        for i in self.online_players:
            player = self.get_player(i)
            if player.is_on_planet():
                players_to_update.add(player)
        for player in players_to_update:
            if player.is_updating() or not player.can_be_updated():
                continue
            image, components = await self.make_game_message(
                player.get_id(), do_actions=False
            )
            await player.get_game_message().edit(image, components=components)

    async def disconnect_player(self, player_id, delete=False):
        del self.online_players[player_id]
        star_name, planet_number, _ = self.get_location(player_id)
        star = self.get_star(star_name)
        if delete:
            star.remove_player(player_id)
        else:
            star.remove_online_player(player_id)
        star.get_planet(planet_number).remove_online_player(player_id)
        if self.is_on_planet(player_id):
            y, x = self.get_coords(player_id)
            self.get_field_by_player(player_id)[y][x].remove(
                self.get_player(player_id)
            )
            self.get_star(star_name).get_planet(
                planet_number
            ).remove_online_player(player_id)
        await self.get_player(player_id).get_game_message().delete()
        await self.update_by_player(player_id)
        if star.get_all_players_number() == 0:
            del self.stars[star.get_name()]
        await self.update_cosmos(star_name, True, player_id)

    async def choose_emoji(self, inter):
        allowed_emojis = [
            "😀",
            "😃",
            "😄",
            "😁",
            "😆",
            "😅",
            "🤣",
            "😂",
            "🙂",
            "🙃",
            "\U0001fae0",
            "😉",
            "😊",
            "😇",
            "🥰",
            "😍",
            "🤩",
            "😘",
            "😗",
            "☺",
            "😚",
            "😙",
            "🥲",
            "😋",
            "😛",
            "😜",
            "🤪",
            "😝",
            "🤑",
            "🤗",
            "🤭",
            "\U0001fae2",
            "\U0001fae3",
            "🤫",
            "🤔",
            "\U0001fae1",
            "🤐",
            "🤨",
            "😐",
            "😑",
            "😶",
            "\U0001fae5",
            "😶",
            "😏",
            "😒",
            "🙄",
            "😬",
            "😮",
            "🤥",
            "\U0001fae8",
            "😌",
            "😔",
            "😪",
            "🤤",
            "😴",
            "😷",
            "🤒",
            "🤕",
            "🤧",
            "🥴",
            "😵",
            "😵",
            "🤯",
            "🤠",
            "🥳",
            "🥸",
            "😎",
            "🤓",
            "🧐",
            "😕",
            "\U0001fae4",
            "😟",
            "🙁",
            "☹",
            "😮",
            "😯",
            "😲",
            "😳",
            "🥺",
            "\U0001f979",
            "😦",
            "😧",
            "😨",
            "😰",
            "😥",
            "😢",
            "😭",
            "😱",
            "😖",
            "😣",
            "😞",
            "😓",
            "😩",
            "😫",
            "🥱",
            "😤",
            "😠",
            "😡",
            "🤬",
            "😈",
            "👿",
            "🧌",
        ]
        global choosing_emoji
        choosing_emoji.add(inter.author.id)
        asking_for_emoji_message = await inter.channel.send(
            "Отправьте свой эмодзи\n"
            "(Разработка кузомира приостановлена и не планируется)"
        )
        emoji = None
        invalid_emoji_message = None
        try:
            while True:
                message = await self.bot.wait_for("message", timeout=120)
                if message.author != inter.author:
                    continue
                emoji = message.content.strip()
                if isinstance(inter.channel, disnake.TextChannel):
                    try:
                        await message.delete()
                    except PermissionError as error:
                        await inter.channel.send(
                            "(У бота недостаточно прав на удаление сообщений)",
                            delete_after=5,
                        )
                        print(error)
                if emoji in allowed_emojis:
                    break
                if invalid_emoji_message:
                    await invalid_emoji_message.delete()
                invalid_emoji_message = await inter.followup.send(
                    "Этот эмодзи нельзя использовать. "
                    "Пожалуйста, выбирайте простые, круглые эмодзи "
                    'из первой вкладки "Люди".',
                    delete_after=15,
                    ephemeral=True,
                )
        except asyncio.TimeoutError:
            if invalid_emoji_message:
                await invalid_emoji_message.delete()
            await inter.channel.send("Время ожидания истекло", delete_after=5)
        choosing_emoji.remove(inter.author.id)
        await asking_for_emoji_message.delete()
        return emoji

    # Методы про игроков:
    def change_player_mode(self, player_id, mode):
        self.get_player(player_id).set_mode(mode)

    def is_right_player(self, player_id, message):
        if player_id not in self.all_players:
            return False
        return self.get_game_message(player_id) == message

    def get_player(self, player_id) -> Player:
        return self.all_players[player_id]

    def is_on_planet(self, player_id) -> bool:
        return self.get_player(player_id).is_on_planet()

    def get_coords(self, player_id):
        return self.get_player(player_id).get_coords()

    def get_location(self, player_id):
        return self.get_player(player_id).get_location()

    def get_game_message(self, player_id) -> disnake.Message:
        return self.get_player(player_id).get_game_message()

    def get_player_emoji(self, player_id):
        return self.get_player(player_id).get_emoji()

    def get_star_name_of_a_player(self, player_id):
        return self.get_player(player_id).get_star_name()

    def get_players_without_a_star(self):
        output = []
        for i in self.online_players:
            player = self.get_player(i)
            if not player.get_star_name():
                output.append(player)
        return output

    def get_players_of_a_star(self, star_name):
        star = self.get_star(star_name)
        output = []
        for i in star.get_online_players():
            player = self.get_player(i)
            output.append(player)
        return output

    def get_all_players(self):
        return self.all_players

    # Методы про планеты:
    def get_field_by_player(self, player_id):
        return self.get_field_by_location(*self.get_location(player_id))

    def get_field_by_location(self, star_name, planet_number, planet_level):
        return (
            self.stars[star_name]
            .get_planet(planet_number)
            .get_field(planet_level)
        )

    def get_players_on_planet(self):
        output = []
        for i in self.online_players:
            player = self.get_player(i)
            if player.is_on_planet():
                output.append(player)
        return output

    # Методы про звёзды
    def get_star(self, star_name) -> Star:
        return self.stars[star_name]

    def get_star_of_a_player(self, player_id) -> Star:
        return self.get_star(self.get_player(player_id).get_star_name())

    def add_star(self, star: Star, player_id):
        star.add_player(player_id)
        self.stars[star.get_name()] = star
        self.get_player(player_id).set_star_name(star.get_name())

    def is_star_limit_reached(self):
        return len(self.stars) >= self.star_limit

    def is_dead(self, player_id):
        return self.get_player(player_id).is_dead()

    # Методы перемещения по космосу
    def go_to_deep_space(self, player_id):
        # добавить проверку на топливо/что-то подобное
        star = self.get_star_of_a_player(player_id)
        star.remove_player(player_id)
        if star.get_all_players_number() == 0:
            del self.stars[star.get_name()]
        player = self.get_player(player_id)
        player.set_star_name(None)

    def go_to_a_star(self, star_name, player_id):
        star = self.get_star(star_name)
        star.add_player(player_id)
        self.get_player(player_id).set_star_name(star.get_name())

    def leave_planet(self, player_id):
        field = self.get_field_by_player(player_id)
        player = self.get_player(player_id)
        y, x = player.get_coords()
        field[y][x].remove(player)
        if player.get_ship():
            field[y][x].remove(player.get_ship())
        star_name, planet, _ = player.get_location()
        self.get_star(star_name).get_planet(planet).remove_online_player(
            player_id
        )
        player.set_planet_level(None)
        player.set_planet_number(None)

    def land(self, player_id, planet_number):
        planet = self.get_star_of_a_player(player_id).get_planet(planet_number)
        if not planet.is_generated(0):
            planet.generate_level(0)
        player = self.get_player(player_id)
        planet.land_player(player)
        player.set_planet_number(planet_number)
        player.set_planet_level(0)


class Item:
    def __init__(
        self,
        name,
        showed_name,
        emoji,
        description=None,
        actions_on_use=None,
        quantity=1,
        damage=5,
        statistics=None,
        showed_statistics=None,
        stack=1,
        capacity=0,
        inside_items=None,
    ):
        self.name = name
        self.showed_name = showed_name
        self.emoji = emoji
        self.description = description
        if actions_on_use is None:
            actions_on_use = dict()
        self.actions_on_use = actions_on_use
        self.quantity = quantity
        self.damage = damage
        if statistics is None:
            statistics = dict()
        self.statistics = statistics
        if showed_statistics is None:
            showed_statistics = dict()
        self.showed_statistics = showed_statistics
        self.stack = stack
        self.capacity = capacity
        if inside_items is None:
            inside_items = []
        self.inside_items = inside_items

    def get_copy(self):
        inside_items = []
        for item in self.inside_items:
            inside_items.append(item.get_copy())
        return Item(
            self.name,
            self.showed_name,
            self.emoji,
            self.description,
            self.actions_on_use.copy(),
            self.quantity,
            self.damage,
            self.statistics.copy(),
            self.showed_statistics.copy(),
            self.stack,
            self.capacity,
            inside_items,
        )

    def is_usable(self, player):
        actions = self.actions_on_use
        for action_name in actions:
            if action_name == "change_player_statistics":
                statistics = player.get_statistics()
                for key, delta, max_value in actions[action_name]:
                    if statistics[key] + delta > max_value:
                        return False
        return bool(self.actions_on_use)

    def get_showed_name(self):
        return self.showed_name

    def get_capacity(self):
        return self.capacity

    def get_stack(self):
        return self.stack

    def get_name(self):
        return self.name

    def get_emoji(self):
        return self.emoji

    def get_description(self):
        return self.description

    def get_quantity(self):
        return self.quantity

    def set_quantity(self, quantity):
        self.quantity = quantity

    def change_quantity(self, delta):
        self.quantity += delta

    def get_actions_on_use(self):
        return self.actions_on_use

    def get_damage(self):
        return self.damage

    def get_statistics(self):
        return self.statistics

    def get_showed_statistics(self):
        return self.showed_statistics

    def get_inside_items(self):
        return self.inside_items


class Inventory:
    def __init__(self, items=None, bag=None):
        if items is None:
            items = list()
        self.items = items
        self.bag = bag
        self.capacity = 1

    def put(
        self, item, player
    ):  # добавляет копию предмета !нужен правильный стак!
        main_item = player.get_main_item()
        stack = item.get_stack()
        quantity = item.get_quantity()
        for i in self.items:
            if i.get_name() == item.get_name():
                quantity2 = i.get_quantity()
                can_be_put = stack - quantity2
                if main_item is None:
                    player.set_main_item(i)
                if quantity <= can_be_put:
                    i.change_quantity(quantity)
                    return 0
                i.set_quantity(stack)
                quantity -= can_be_put
        if len(self.items) < self.capacity:
            new_item = item.get_copy()
            new_item.set_quantity(quantity)
            self.items.append(new_item)
            if main_item is None:
                player.set_main_item(new_item)
            return 0
        return quantity

    # def remove_item(self, item):
    #     if item in self.items:
    #         self.items.remove(item)
    #     elif item == self.bag:
    #         self.bag = None
    #     elif self.bag and item in self.bag.get_inside_items():
    #         self.bag.get_inside_items().remove(item)

    def change_quantity(self, item, delta):
        for i in self.get_items():
            if i == item:
                item.change_quantity(delta)
                if not item.get_quantity():
                    self.items.remove(item)
                    return
        if self.bag == item:
            item.change_quantity(delta)
            if not item.get_quantity():
                self.bag = None
                return
        if self.bag:
            for i in self.bag.get_inside_items():
                if i == item:
                    item.change_quantity(delta)
                    if not item.get_quantity():
                        self.bag.get_inside_items().remove(item)
                        return

    def get_capacity(self):
        return self.capacity

    def get_items(self):
        return self.items

    def get_bag(self):
        return self.bag

    def get_bag_items(self):
        return self.bag.get_inside_items()

    def get_all_items(self):
        all_items = []
        for i in self.items:
            all_items.append(i)
        if self.bag:
            all_items.append(bag)
            for i in self.bag.get_inside_items():
                all_items.append(i)
        return all_items

    def has_item(self, item):
        for i in self.items:
            if i == item:
                return True
        if self.bag:
            if item == self.bag:
                return True
            for i in self.bag.get_inside_items():
                if i == item:
                    return True
        return False

    def __len__(self):
        output = len(self.items)
        if self.bag:
            output += self.bag.get_inside_items()
        return output


class KuzoworldCog02(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #  @commands.slash_command(name="кузомир-обновить", description="дебаг-команда, если зависло")
    async def manual_update(self, inter: disnake.ApplicationCommandInteraction):
        global game
        if not game:
            await inter.response.send_message("Игра выключена", ephemeral=True)
            return
        player = game.get_player(inter.author.id)
        player.turn_updates_on()
        await game.update_one_player(inter.author.id)
        try:
            await inter.response.send_message(
                "Ваше окно обновлено", ephemeral=True
            )
        except Exception as error:
            await inter.response.send_message(
                "Что-то пошло не так", ephemeral=True
            )
            print(error)

    @commands.slash_command(name="emoji-world", description="незаконченная рпг")
    async def kuzoworld(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            "Загрузка Кузомира 0.2...", delete_after=0
        )

        global game

        if not game:
            # в будущем здесь будет загрузка из kuzoworld.txt
            game = Game(self.bot)
            _ = asyncio.create_task(game.tick_loop())
            _ = asyncio.create_task(game.inventory_loop())
        await game.connect_player(inter)

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith(ID):
            return

        global generated_stars
        global choosing_item

        if not game:
            await inter.response.send_message(
                "Игра сейчас выключена. Вы можете включить её через /кузомир_v02",
                ephemeral=True,
            )
            return
        if not game.is_right_player(inter.author.id, inter.message):
            await inter.response.send_message(
                "Это не ваше окно. Чтобы открыть своё, используйте /кузомир_v02",
                ephemeral=True,
            )
            return
        action = inter.component.custom_id[len(ID) :]
        player_id = inter.author.id
        if action == "reset":
            await inter.message.delete()
            await game.connect_player(inter)
            return
        if action == "update":
            choosing_item.pop(player_id, None)
            player = game.get_player(player_id)
            player.turn_updates_on()
            inventory = player.get_inventory()
            if not inventory.has_item(player.get_main_item()):
                player.set_main_item(None)
            image, components = await game.make_game_message(player_id)
            await inter.response.edit_message(image, components=components)
        elif "add_star_" in action:
            number = int(action[9:])
            star = generated_stars[player_id][number]
            if (
                star.get_type() != "spawn"
                and not game.get_player(player_id).have_landed_before()
            ):
                await inter.response.send_message(
                    'В ваше первое приземление вы можете выбрать только звезду типа "Приют".',
                    ephemeral=True,
                )
                return
            game.get_player(player_id).turn_updates_on()
            game.add_star(star, player_id)
            image, components = await game.make_game_message(player_id)
            del generated_stars[player_id]
            await inter.response.edit_message(image, components=components)
            await game.update_cosmos(None, True, player_id)
        elif action == "generate_star":
            game.get_player(player_id).turn_updates_off()
            stars = []
            for _ in range(2):
                stars.append(generate_star())
            stars.append(generate_star(star_type="spawn"))
            random.shuffle(stars)
            output = "Вы можете полететь лишь на одну из трёх найденных звёзд. На какую вы полетите?\n\n"
            for star in stars:
                output += f"{star.get_emoji()} {star.get_name()}. {star.get_type_name()}\n\n"
            buttons = []
            for i in range(len(stars)):
                star = stars[i]
                buttons.append(
                    ui.Button(
                        label=star.get_name(),
                        style=BLUE,
                        custom_id=ID + f"add_star_{i}",
                    )
                )
            # buttons.append(ui.Button(label="Отмена", style=RED, custom_id=ID + "update"))
            components = [ui.ActionRow(i) for i in buttons]
            generated_stars[player_id] = stars
            await inter.response.edit_message(output, components=components)
        elif action == "deep_space_ask":
            game.get_player(player_id).turn_updates_off()
            await inter.response.edit_message(
                "Если вы улетите, и в системе не останется ни одного игрока, она будет потеряна навсегда.\n"
                "Вы уверены, что хотите улететь?\n"
                "Перелёт ничего не стоит.",
                components=[
                    ui.Button(
                        label="Да", style=GREEN, custom_id=ID + "deep_space"
                    ),
                    ui.Button(label="Нет", style=RED, custom_id=ID + "update"),
                ],
            )
        elif action == "deep_space":
            game.get_player(player_id).turn_updates_on()
            star_name = game.get_star_name_of_a_player(player_id)
            game.go_to_deep_space(player_id)
            image, components = await game.make_game_message(player_id)
            await inter.response.edit_message(image, components=components)
            await game.update_cosmos(star_name, True, player_id)
        elif "go_to_a_star_" in action:
            star_name = action[13:]
            star = game.get_star(star_name)
            if (
                star.get_type() != "spawn"
                and not game.get_player(player_id).have_landed_before()
            ):
                await inter.response.send_message(
                    'В ваше первое приземление вы можете выбрать только звезду типа "Приют".',
                    ephemeral=True,
                )
                return
            game.go_to_a_star(star_name, player_id)
            image, components = await game.make_game_message(player_id)
            await inter.response.edit_message(image, components=components)
            await game.update_cosmos(star_name, True, player_id)
        elif "open_planet_" in action:
            number = int(action[12:])
            game.get_player(player_id).turn_updates_off()
            star = game.get_star_of_a_player(player_id)
            planet = star.get_planet(number)
            if (
                planet.get_type() != "spawn"
                and not game.get_player(player_id).have_landed_before()
            ):
                await inter.response.send_message(
                    'В ваше первое приземление вы можете выбрать только планету типа "Приют".',
                    ephemeral=True,
                )
                return
            output = (
                f"Планета {planet.get_emoji()} {star.get_name()} {planet.get_roman()}\n"
                f"Радиус: {round(planet.get_size() * 15.945)} км. \tУсловия: {planet.get_conditions()}\n"
                f"Игроков: {planet.get_online_players_number()}"
            )
            await inter.response.edit_message(
                output,
                components=[
                    ui.Button(
                        label="Приземлиться",
                        style=GREEN,
                        custom_id=ID + "land_planet_" + str(number),
                    ),
                    ui.Button(
                        label="Вернуться", style=GRAY, custom_id=ID + "update"
                    ),
                ],
            )
        elif "land_planet_" in action:
            await inter.response.edit_message(
                "Выбираем место посадки... (Это займёт некоторое время)",
                components=[],
            )
            # await game.land(player_id, int(action[12:]))
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, game.land, player_id, int(action[12:])
            )
            game.get_player(player_id).turn_updates_on()
            star = game.get_star_of_a_player(player_id)
            await inter.followup.send(
                f"Вы приземлились, {inter.author.mention}", delete_after=5
            )
            await game.update_cosmos(star.get_name())
            await game.update_by_player(player_id, self_update=True)
        elif action == "mid":
            player = game.get_player(player_id)
            player.turn_updates_off()
            star, planet, _ = player.get_location()
            planet = game.get_star(star).get_planet(planet)
            y, x = player.get_coords()
            x = x - planet.get_size() // 2
            y = planet.get_size() // 2 - y
            online = planet.get_online_players_number()
            await inter.response.edit_message(
                f"{player.get_emoji()} {player.get_name()}\n"
                f"X: {x} Y: {y}\n"
                f"Игроков на планете: {online}",
                components=[
                    ui.Button(
                        label="Вернуться",
                        custom_id=ID + "update",
                        style=disnake.ButtonStyle.secondary,
                    ),
                    ui.Button(
                        label="Выйти из игры",
                        custom_id=ID + "leave",
                        style=disnake.ButtonStyle.primary,
                    ),
                    ui.Button(
                        label="Поменять эмодзи",
                        custom_id=ID + "change_emoji",
                        style=disnake.ButtonStyle.primary,
                    ),
                    ui.Button(
                        label="Удалить персонажа",
                        custom_id=ID + "delete_ask",
                        style=disnake.ButtonStyle.danger,
                    ),
                ],
            )
            return
        elif action == "leave":
            game.get_player(player_id).turn_updates_on()
            await game.disconnect_player(player_id)
        elif action == "change_emoji":
            await inter.response.edit_message()
            emoji = await game.choose_emoji(inter)
            if emoji:
                game.get_player(player_id).set_emoji(emoji)
            game.get_player(player_id).turn_updates_on()
            await game.update_by_player(player_id, self_update=True)
        elif action == "delete_ask":
            await inter.response.edit_message(
                "Вы уверены, что хотите полностью удалить своего персонажа?",
                components=[
                    ui.Button(label="Да", style=BLUE, custom_id=ID + "delete"),
                    ui.Button(label="Нет", style=RED, custom_id=ID + "mid"),
                ],
            )
        elif action == "delete":
            await inter.response.edit_message()
            await game.on_death(game.get_player(player_id))
            return
        elif action == "delete_game_message":
            await inter.message.delete()
            return
        elif action == "inventory":
            game.get_player(player_id).turn_updates_off()
            image, components = (
                game.get_inventory_image(player_id),
                game.get_inventory_components(player_id),
            )
            await inter.response.edit_message(image, components=components)
            await game.open_inventory(player_id, None)
        elif action in [
            "use_item",
            "move_item",
            "drop_item",
            "split_item",
            "merge_item",
            "drop_item_one",
        ]:
            await game.do_player_action(action, player_id)
            if player_id in choosing_item:
                image, components = (
                    game.get_inventory_image(
                        player_id, choosing_item[player_id]
                    ),
                    game.get_inventory_components(
                        player_id, choosing_item[player_id]
                    ),
                )
                await inter.response.edit_message(image, components=components)
            else:
                image, components = await game.make_game_message(player_id)
                await inter.response.edit_message(image, components=components)
        elif action == "craft" or action in [
            "use_mode",
            "build_mode",
            "attack_mode",
        ]:
            return
        else:
            await game.do_player_action(action, player_id)
            if player_id in choosing_item:
                image, components = (
                    game.get_inventory_image(
                        player_id, choosing_item[player_id]
                    ),
                    game.get_inventory_components(
                        player_id, choosing_item[player_id]
                    ),
                )
                await inter.response.edit_message(image, components=components)
            else:
                image, components = await game.make_game_message(player_id)
                await inter.response.edit_message(image, components=components)
                await game.update_by_player(player_id)
        player = game.get_player(player_id)
        if player.check_death():
            await game.on_death(player)


ITEMS = {
    "mushroom": Item(
        name="mushroom",
        showed_name="Гриб",
        emoji="🍄",
        description="Гриб. Вкусный, наверное.",
        actions_on_use={
            "change_player_statistics": [("hunger", 30, 130)],
            "change_quantity": -1,
        },
        stack=3,
    )
}

THINGS = {
    "tree": Structure(name="tree", emoji="🌳", collision=True),
    "mushroom": Structure(
        name="mushroom",
        emoji="🍄",
        collision=True,
        actions_on_use={"give": ITEMS["mushroom"], "replace": None},
    ),
    "cactus": Structure(
        name="cactus",
        emoji="🌵",
        actions_on_near={"change_player_statistics": [("health", -3, 100)]},
        collision=True,
    ),
    "hole_down": Structure(
        name="hole", emoji="🕳️", actions_on_use={"change_level": -1}
    ),
}


def setup(bot):
    bot.add_cog(KuzoworldCog02(bot))
