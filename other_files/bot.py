import logging
import math
import os
import sqlite3
import subprocess
import tempfile
import time
from random import sample

import discord
import youtube_dl
from discord import Activity, ActivityType, Status
from discord.commands import Option
from discord.ext import commands

bot = commands.Bot(
    command_prefix="/",
    intents=discord.Intents.all(),
    activity=discord.Activity(
        type=discord.ActivityType.watching, name="на унижения куза."
    ),
    status=discord.Status.dnd,
)

db_file = "ratings.db"
owner = 672136434534318122
admins_list = [672136434534318122, 393779108708089856]
BOMB = ":boom:"
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
]
if os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
else:
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("CREATE TABLE ratings (user_id INTEGER, rating REAL)")
    conn.commit()

c.execute(
    "CREATE TABLE IF NOT EXISTS cooldowns (user_id INTEGER PRIMARY KEY, last_used REAL)"
)

ffmpeg_options = {
    "options": "-vn",
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
}
BOMB = ":boom:"
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
]

logging.basicConfig(level=logging.INFO)  # Уровень логирования INFO


def discord_minesweeper(side_x, side_y, bombs):
    if side_x > 99:
        return ["слишком большое поле"]
    if bombs == "easy":
        bombs = round(side_x * side_y * 0.101)
    elif bombs == "normal":
        bombs = round(side_x * side_y * 0.15625)
    elif bombs == "hard":
        bombs = round(side_x * side_y * 0.20625)
    elif bombs == "extreme":
        bombs = round(side_x * side_y * 0.3)
    field = [[0 for i in range(side_x)] for j in range(side_y)]
    coords = sample(range(side_x * side_y), bombs)
    for i in coords:
        y = i // side_x
        x = i % side_x
        field[y][x] = BOMB
        for x_offset in range(-1, 2):
            for y_offset in range(-1, 2):
                if not (0 <= x + x_offset < side_x) or not (
                    0 <= y + y_offset < side_y
                ):
                    continue
                if type(field[y + y_offset][x + x_offset]) is int and (
                    x_offset != 0 or y_offset
                ):
                    field[y + y_offset][x + x_offset] += 1
    for y in range(side_y):
        for x in range(side_x):
            if type(field[y][x]) is int:
                field[y][x] = "||" + numbers[field[y][x]] + "||"
            else:
                field[y][x] = "||" + BOMB + "||"
    return ["".join(i) for i in field]


@bot.slash_command(
    name="бастбуст", description="бастбуст!", guild_ids=[955168680474443777]
)
async def bassboost(
    ctx,
    boost_level: Option(int, "Уровень басс-буста в децибелах.", required=True),
):
    if not bot.voice_clients:
        embed = discord.Embed(
            title="Ошибка",
            description="Бот не подключен к голосовому каналу.",
            color=discord.Color.red(),
        )
        await ctx.respond(embed=embed)
        return

    voice_client = bot.voice_clients[0]
    if not voice_client.is_playing():
        embed = discord.Embed(
            title="Ошибка",
            description="В данный момент ничего не воспроизводится.",
            color=discord.Color.red(),
        )
        await ctx.respond(embed=embed)
        return

    try:
        current_audio_source = voice_client.source
        audio_data = current_audio_source.read()
        boosted_audio_data = apply_bass_boost(audio_data, boost_level)
        voice_client.source = discord.PCMVolumeTransformer(
            discord.AudioData(
                boosted_audio_data,
                current_audio_source._channels,
                current_audio_source._sample_width,
                current_audio_source._frame_rate,
            ),
            volume=voice_client.source.volume,
        )
        embed = discord.Embed(
            title="Успех",
            description=f"Басс-буст успешно применен на {boost_level} дБ.",
            color=discord.Color.green(),
        )
        await ctx.respond(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="Ошибка",
            description=f"Произошла ошибка при применении басс-буста: {e!s}",
            color=discord.Color.red(),
        )
        await ctx.respond(embed=embed)


# Функция для применения басс-буста
def apply_bass_boost(audio_data, boost_level):
    # Создаем временный файл для сохранения аудиоданных
    temp_input_path = tempfile.NamedTemporaryFile(
        suffix=".mp3", delete=False
    ).name
    with open(temp_input_path, "wb") as f:
        f.write(audio_data)

    # Создаем временный файл для сохранения обработанного аудио
    temp_output_path = tempfile.NamedTemporaryFile(
        suffix=".mp3", delete=False
    ).name

    # Команда для применения басс-буста с помощью ffmpeg
    ffmpeg_command = [
        "ffmpeg",
        "-i",
        temp_input_path,
        "-af",
        f"bass=g={boost_level}",
        "-vn",
        "-y",
        temp_output_path,
    ]

    # Запускаем ffmpeg
    try:
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        # Обработка ошибок
        print("Ошибка при применении басс-буста:", e)
        return None
    finally:
        # Удаляем временные файлы
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)

    # Читаем обработанные аудиоданные
    with open(temp_output_path, "rb") as f:
        processed_audio_data = f.read()

    return processed_audio_data


@bot.slash_command(
    description="Зарегистрирует тебя!", id_server=955168680474443777
)
async def register(ctx):
    user_id = ctx.author.id
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ratings WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result is not None:
        await ctx.respond("Вы уже зарегистрированы в системе рейтинга.")
    else:
        cursor.execute("INSERT INTO ratings VALUES (?, ?)", (user_id, 4))
        conn.commit()
        await ctx.respond(
            "Вы успешно зарегистрировались в системе рейтинга. Ваш начальный рейтинг: 4."
        )


@bot.slash_command(
    description="Посмотреть чужой рейтинг", id_server=955168680474443777
)
async def rating(ctx: discord.ApplicationContext, member: discord.Member):
    if member is None:
        user_id = ctx.author.id
    else:
        user_id = member.id
    cursor = conn.cursor()
    cursor.execute("SELECT rating FROM ratings WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result is not None:
        rating = round(result[0], 4)
        embed = discord.Embed(color=0x00FF00)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1041083432752652378/1106704330763018250/image.png"
        )
        embed.set_author(name=member, icon_url=member.avatar.url)
        embed.add_field(name="Рейтинг", value=rating)
        place = get_place(user_id, rating)
        embed.add_field(name="Топ", value=place)
        await ctx.respond(embed=embed)
    else:
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name=member, icon_url=member.avatar.url)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1041083432752652378/1106704330763018250/image.png"
        )
        embed.add_field(
            name="Ошибка",
            value="Пользователь не зарегистрирован в системе рейтинга.",
        )
        await ctx.respond(embed=embed)


def get_place(user_id, rating):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, rating FROM ratings")
    results = cursor.fetchall()
    results.sort(key=lambda x: x[1], reverse=True)
    index = -1
    for i, (uid, rat) in enumerate(results):
        if uid == user_id:
            index = i
            break
    if index == -1:
        return "Неизвестно"
    return str(index + 1)


class ControlButtons(discord.ui.View):
    def __init__(self, voice_client: discord.VoiceClient):
        super().__init__()
        self.voice_client = voice_client
        self.queue = []
        self.current = None
        self.paused = False

    @discord.ui.button(label="⏯", style=discord.ButtonStyle.blurple)
    async def toggle_pause(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.voice_client.is_playing():
            self.voice_client.pause()
            self.paused = True
            button.style = discord.ButtonStyle.red
            button.label = "▶"
            await interaction.response.send_message("Пауза", ephemeral=True)
        elif self.voice_client.is_paused():
            self.voice_client.resume()
            self.paused = False
            button.style = discord.ButtonStyle.blurple
            button.label = "⏯"
            await interaction.response.send_message(
                "Продолжаем", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Нет активного трека", ephemeral=True
            )

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.blurple)
    async def skip(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if self.queue:
            self.current = self.queue.pop(0)
            self.voice_client.play(
                discord.FFmpegPCMAudio(self.current["url"], **ffmpeg_options)
            )
            await interaction.response.send_message(
                f"Пропускаем текущий трек и играем {self.current['title']}",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Нет треков в очереди", ephemeral=True
            )

    @discord.ui.button(label="🗑", style=discord.ButtonStyle.blurple)
    async def clear(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.queue.clear()
        await interaction.response.send_message(
            "Очередь очищена", ephemeral=True
        )

    @discord.ui.button(label="🔇", style=discord.ButtonStyle.blurple)
    async def disconnect(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await self.voice_client.disconnect()
        await interaction.response.send_message("Бот отключен", ephemeral=True)


@bot.slash_command(description="Играть музыку!", id_server=955168680474443777)
async def play(ctx, url: Option(str, "Ссылка на видео.", required=True)):
    if not bot.voice_clients:
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()
        view = ControlButtons(bot.voice_clients[0])
    else:
        view = bot.voice_clients[0].view
    voice_client = bot.voice_clients[0]
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "source_address": "0.0.0.0",
        "nocheckcertificate": True,
    }
    ffmpeg_options = {
        "options": "-vn",
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info["title"]
            url = info["formats"][0]["url"]
            author = info["uploader"]
            duration = info["duration"]
            minutes, seconds = divmod(duration, 60)
            duration = f"{minutes:02}:{seconds:02}"
            track = {
                "title": title,
                "url": url,
                "author": author,
                "duration": duration,
            }
            if voice_client.is_playing():
                view.queue.append(track)
                await ctx.respond(
                    embed=discord.Embed(
                        title="Добавлено в очередь",
                        description=f"{title} от {author} ({duration})",
                        color=discord.Color.blue(),
                    ),
                    view=view,
                )
            else:
                view.current = track
                voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options))
                activity = Activity(
                    type=ActivityType.listening, name=f"{title}"
                )
                await bot.change_presence(activity=activity, status=Status.dnd)
                await ctx.respond(
                    embed=discord.Embed(
                        title="Сейчас играет",
                        description=f"{title} от {author} ({duration})",
                        color=discord.Color.blue(),
                    ),
                    view=view,
                )
    except youtube_dl.utils.DownloadError:
        embed = discord.Embed(
            title="Ошибка",
            description="Не удалось скачать видео по ссылке. Пожалуйста, проверьте, что ссылка правильная и доступная.",
            color=discord.Color.red(),
        )
        await ctx.respond(embed=embed)
    except discord.errors.ClientException:
        embed = discord.Embed(
            title="Ошибка",
            description="Не удалось воспроизвести аудио из видео.",
            color=discord.Color.red(),
        )
        await ctx.respond(embed=embed)
    except Exception:
        embed = discord.Embed(
            title="Ошибка",
            description="Произошла неизвестная ошибка. Пожалуйста, попробуйте еще раз позже.",
            color=discord.Color.red(),
        )
        await ctx.respond(embed=embed)


@bot.slash_command(
    description="Отключает бота с канала!", guild_ids=[955168680474443777]
)
async def leave(ctx):
    await ctx.voice_client.disconnect()
    activity = Activity(type=ActivityType.watching, name="на унижения куза.")
    await bot.change_presence(activity=activity, status=Status.dnd)
    embed = discord.Embed(
        title="Успех",
        description="Бот вышел из канала!",
        color=discord.Color.green(),
    )
    await ctx.respond(embed=embed)


@bot.slash_command(description="Оценить!", id_server=955168680474443777)
async def rate(
    ctx: discord.ApplicationContext, member: discord.Member, score: int
):
    rater_id = ctx.author.id
    rated_id = member.id
    if rater_id == rated_id:
        await ctx.respond("Вы не можете оценить себя.")
        return
    cursor = conn.cursor()
    cursor.execute("SELECT rating FROM ratings WHERE user_id = ?", (rater_id,))
    rater_result = cursor.fetchone()
    cursor.execute("SELECT rating FROM ratings WHERE user_id = ?", (rated_id,))
    rated_result = cursor.fetchone()
    if rater_result is not None and rated_result is not None:
        cursor.execute(
            "SELECT last_used FROM cooldowns WHERE user_id = ?", (rater_id,)
        )
        result = cursor.fetchone()
        if result is None:
            pass
        else:
            last_used = result[0]
            current_time = time.time()
            difference = current_time - last_used
            cooldown_time = 3600
            if difference <= cooldown_time:
                await ctx.respond(
                    f"Подожди. Ты на кулдауне. Попробуй снова через {math.ceil(cooldown_time - difference)} секунд"
                )
                return

        PR = rated_result[0]
        RR = rater_result[0]
        if 1 <= score <= 5:
            K = 0.03
            NR = (PR + score * (RR / PR * K)) / (1 + (RR / PR * K))
            NR = round(NR, 4)
            cursor.execute(
                "UPDATE ratings SET rating = ? WHERE user_id = ?",
                (NR, rated_id),
            )
            conn.commit()
            await ctx.respond(
                f"Вы успешно оценили пользователя {member} на {score} баллов. Его новый рейтинг: {NR}."
            )
            if result is None:
                cursor.execute(
                    "INSERT INTO cooldowns VALUES (?, ?)",
                    (rater_id, time.time()),
                )
                conn.commit()
            else:
                cursor.execute(
                    "UPDATE cooldowns SET last_used = ? WHERE user_id = ?",
                    (current_time, rater_id),
                )
                conn.commit()
        else:
            await ctx.respond("Оценка должна быть в диапазоне от 1 до 5.")
            return
    else:
        await ctx.respond(
            "Один из пользователей не зарегистрирован в системе рейтинга."
        )
        return


@rate.error
async def rate_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.respond("Ты должен указать кого хочешь оценить..")
    elif isinstance(error, commands.BadArgument):
        await ctx.respond("Ты должен указать действительного человека..")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(
            f"Подожди. Ты на кулдауне. Попробуй снова через {math.ceil(error.retry_after)} секунд"
        )
    else:
        raise error


@bot.slash_command(
    description="Посмотреть топ-10!", id_server=955168680474443777
)
async def toprate(ctx):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, rating FROM ratings ORDER BY rating DESC LIMIT 10"
    )
    results = cursor.fetchall()
    embed = discord.Embed(
        title="Топ-10 пользователей по рейтингу", color=0x00FF00
    )
    for i, (user_id, rating) in enumerate(results, start=1):
        emoji = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"][
            i - 1
        ]
        user = bot.get_user(user_id)
        rating = round(rating, 4)
        if user is not None:
            embed.add_field(
                name=f"{emoji} {user.name}",
                value=f"{rating} 分。",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{emoji} Ноунейм.", value=f"{rating} 分。", inline=False
            )
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1041083432752652378/1106698242542022787/1.png"
    )
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/1041083432752652378/1106704330763018250/image.png"
    )
    await ctx.respond(embed=embed)


@bot.slash_command(
    description="Удалить чужой рейтинг!", id_server=955168680474443777
)
async def delrating(ctx, member: discord.Member, amount: float):
    user = ctx.author
    user_roles = user.roles
    if discord.utils.get(user_roles, id=1193862968195170334):
        c.execute("SELECT rating FROM ratings WHERE user_id = ?", (member.id,))
        rating = c.fetchone()
        if rating is None:
            await ctx.respond(f"{member.mention} не имеет рейтинга.")
        else:
            new_rating = rating[0] - amount
            c.execute(
                "UPDATE ratings SET rating = ? WHERE user_id = ?",
                (new_rating, member.id),
            )
            conn.commit()
            await ctx.respond(
                f"Рейтинг {member.mention} понижен на {amount} и теперь равен {new_rating}."
            )
    else:
        await ctx.respond("У вас нет прав.")


@bot.slash_command(
    description="Добавить чужой рейтинг!", id_server=955168680474443777
)
async def addrating(ctx, member: discord.Member, amount: float):
    user = ctx.author
    user_roles = user.roles
    if discord.utils.get(user_roles, id=1193862968195170334):
        c.execute("SELECT rating FROM ratings WHERE user_id = ?", (member.id,))
        rating = c.fetchone()
        if rating is None:
            await ctx.respond(f"{member.mention} не имеет рейтинга.")
        else:
            new_rating = rating[0] + amount
            c.execute(
                "UPDATE ratings SET rating = ? WHERE user_id = ?",
                (new_rating, member.id),
            )
            conn.commit()
            await ctx.respond(
                f"Рейтинг {member.mention} увеличен на {amount} и теперь равен {new_rating}."
            )
    else:
        await ctx.respond("У вас нет прав")


@bot.slash_command(description="пон!", id_server=955168680474443777)
async def write(ctx, channel: discord.TextChannel, message: str):
    user = ctx.author
    user_roles = user.roles
    if discord.utils.get(user_roles, id=1193862968195170334):
        await ctx.delete()
        await channel.send(message)
    else:
        await ctx.send("У вас нет прааааав.")


@bot.slash_command(description="Список команд!", id_server=955168680474443777)
async def help(ctx):
    embed = discord.Embed(title="Список команд", color=0x00FF00)
    embed.set_footer(
        text="ССРФ",
        icon_url="https://cdn.discordapp.com/attachments/1041083432752652378/1106704330763018250/image.png",
    )
    embed.add_field(name="/register", value="зарегистрироваться", inline=True)
    embed.add_field(
        name="/rate", value="оценить, задержка в 1 час", inline=True
    )
    embed.add_field(name="/toprate", value="топ-10 по рейтингу", inline=True)
    embed.add_field(
        name="/rating", value="узнать чей-либо рейтинг.", inline=True
    )
    await ctx.respond(embed=embed)


@bot.slash_command(
    description="Показать задержку бота в миллисекундах",
    guild_ids=[955168680474443777],
)
async def ping(ctx):
    embed = discord.Embed(title="Пинг", color=0x00FF00)
    embed.set_footer(
        text="ССРФ",
        icon_url="https://cdn.discordapp.com/attachments/1041083432752652378/1106704330763018250/image.png",
    )
    milliseconds = bot.latency * 1000
    milliseconds = f"{milliseconds:.3f}"
    embed.add_field(name="Задержка", value=f"{milliseconds} мс.", inline=True)
    await ctx.respond(embed=embed)


@bot.slash_command(
    name="отключить",
    description="Отключить бота!",
    guild_ids=[955168680474443777],
)
async def turn_off(ctx):
    if ctx.author.id == owner:
        embed = discord.Embed(
            title="Отключение бота",
            description="Бот отключается...",
            color=discord.Color.red(),
        )
        await ctx.respond(embed=embed)
        await bot.close()
    elif ctx.author.id in admins_list:
        await ctx.respond(
            "Отключить бота может только владелец, а вы - администратор."
        )
    else:
        await ctx.respond("Отключить бота может только владелец.")


@bot.slash_command(
    name="анализ",
    description="Анализ Любого канала!",
    guild_ids=[955168680474443777],
)
async def analyze(ctx, channel: discord.TextChannel):
    try:
        await ctx.respond(
            f"Анализ {channel.mention}. Подождите несколько минут."
        )
    except ValueError:
        await ctx.send("Некорректный канал!")
        return

    async with ctx.typing():
        messages = await channel.history(limit=None).flatten()
        total_messages = len(messages)
        last_author = messages[0].author
        last_date = messages[0].created_at
        last_text = messages[0].content
        authors = {}

        for message in messages:
            if message.author not in authors:
                authors[message.author] = 1
            else:
                authors[message.author] += 1
        authors = dict(
            sorted(authors.items(), key=lambda item: item[1], reverse=True)
        )

    embed = discord.Embed(
        title=f"Анализ канала {channel.name}", color=discord.Color.blue()
    )
    embed.description = f"Всего сообщений: **{total_messages}**\nПоследнее сообщение от **{last_author}** в **{last_date.strftime('%d.%m.%Y %H:%M')}**:\n> {last_text}"
    embed.set_footer(
        text=f"Запрос от {ctx.author}", icon_url=ctx.author.avatar.url
    )

    rank = 1
    for author, count in authors.items():
        if rank > 10:
            break
        emoji = (
            "🥇"
            if rank == 1
            else "🥈"
            if rank == 2
            else "🥉"
            if rank == 3
            else "🏅"
        )
        embed.add_field(
            name=f"{emoji} {rank}. {author}",
            value=f"{count} сообщений",
            inline=False,
        )
        rank += 1

    await ctx.send(embed=embed)


@bot.slash_command(
    name="сапер",
    description="Генерация игрового поля!",
    guild_ids=[955168680474443777],
)
async def animal_command(
    ctx: discord.ApplicationContext,
    размер: discord.Option(int, choices=["8", "16", "30", "32"]),
    сложность: discord.Option(
        str, choices=["easy", "normal", "hard", "extreme"]
    ),
    ширина: discord.Option(int, required=False),
    высота: discord.Option(int, required=False),
):
    if ширина is not None and высота is not None:
        side_x = ширина
        side_y = высота
    else:
        side_x = размер
        side_y = размер
    bombs = сложность  # Change this to set the difficulty level
    minesweeper_grid = discord_minesweeper(side_x, side_y, bombs)
    await ctx.respond(f"Поле для игры в сапер: `{side_x}`х`{side_y}`!")
    for line in minesweeper_grid:
        await ctx.send(line)


bot.run(
    "MTIzMjM3NzI5NzYzMDEzNDI3Mw.GweDPS.61Bwc499K39lHZh5Ynindf1Jo-MOJoIPfncFMA"
)
