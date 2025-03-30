import asyncio

import disnake
from disnake import ui
from disnake.ext import commands

ID = "safe_"
CORRECT = [
    ui.ActionRow(
        ui.Button(label="7", custom_id=ID + "7"),
        ui.Button(label="8", custom_id=ID + "8"),
        ui.Button(label="9", custom_id=ID + "9"),
    ),
    ui.ActionRow(
        ui.Button(label="4", custom_id=ID + "4"),
        ui.Button(label="5", custom_id=ID + "5"),
        ui.Button(label="6", custom_id=ID + "6"),
    ),
    ui.ActionRow(
        ui.Button(label="1", custom_id=ID + "1"),
        ui.Button(label="2", custom_id=ID + "2"),
        ui.Button(label="3", custom_id=ID + "3"),
    ),
    ui.ActionRow(
        ui.Button(emoji="🔑", custom_id=ID + "key", disabled=True),
        ui.Button(label="0", custom_id=ID + "0"),
        ui.Button(emoji="🔒", disabled=True),
    ),
]

opened_right_now = False
safes_right_now = dict()


def get_content() -> str:
    return open("databases/safe_content.txt", encoding="utf-8").read()


def set_content(content: str) -> None:
    with open("databases/safe_content.txt", "w", encoding="utf-8") as file:
        file.write(content)


class Safe:
    def __init__(self):
        self.numbers = list()
        self.opened = False

    def get_embed(self) -> disnake.Embed:
        embed = disnake.Embed(
            title="Сейф :lock:",
            description=f"Введите код\n{self.get_numbers_string()}",
        )
        return embed

    def get_components(self, correct=0):
        if correct == 1:
            return ui.ActionRow(
                ui.Button(
                    emoji="✅", style=disnake.ButtonStyle.success, disabled=True
                )
            )
        if correct == 0:
            indicator = ui.Button(emoji="🔒", disabled=True)
        else:
            indicator = ui.Button(emoji="❌", disabled=True)
        buttons = [
            ui.ActionRow(
                ui.Button(label="7", custom_id=ID + "7"),
                ui.Button(label="8", custom_id=ID + "8"),
                ui.Button(label="9", custom_id=ID + "9"),
            ),
            ui.ActionRow(
                ui.Button(label="4", custom_id=ID + "4"),
                ui.Button(label="5", custom_id=ID + "5"),
                ui.Button(label="6", custom_id=ID + "6"),
            ),
            ui.ActionRow(
                ui.Button(label="1", custom_id=ID + "1"),
                ui.Button(label="2", custom_id=ID + "2"),
                ui.Button(label="3", custom_id=ID + "3"),
            ),
            ui.ActionRow(
                ui.Button(
                    emoji="🔑",
                    custom_id=ID + "key",
                    disabled=not self.numbers_are_full(),
                ),
                ui.Button(label="0", custom_id=ID + "0"),
                indicator,
            ),
        ]
        return buttons

    def is_opened(self) -> bool:
        return self.opened

    def numbers_are_full(self) -> bool:
        return len(self.numbers) == 3

    def get_numbers_string(self) -> str:
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
        output = ""
        for i in self.numbers:
            output += numbers[int(i)]
        output += ":hash:" * (3 - len(self.numbers))
        return output

    def insert_number(self, number: str) -> None:
        self.numbers.append(number)
        if self.numbers_are_full():
            password = list(
                open("databases/safe_password.txt", encoding="utf-8").read()
            )
            if self.numbers == password:
                self.opened = True

    def clear_numbers(self) -> None:
        self.numbers = list()


class SafeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="safe", description="секретный сейф")
    async def tic_tac_toe(self, inter: disnake.ApplicationCommandInteraction):
        global safes_right_now
        safe = Safe()
        await inter.response.send_message(
            embed=safe.get_embed(), components=safe.get_components()
        )
        message = await inter.original_response()
        safes_right_now[message.id] = safe

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        global opened_right_now
        if not inter.component.custom_id.startswith(ID):
            return
        action = inter.component.custom_id[len(ID) :]

        if inter.message.id not in safes_right_now:
            await inter.response.send_message(
                "Этот сейф был открыт до перезагрузки бота и уже не работает. Откройте "
                "новый с помощью /safe.",
                ephemeral=True,
            )
            return

        safe = safes_right_now[inter.message.id]
        if action == "key":
            if opened_right_now:
                await inter.response.send_message(
                    "Этот сейф уже кем-то открыт в данный момент. "
                    "Подождите некоторое время, чтобы он закрылся снова.",
                    ephemeral=True,
                )
            elif safe.is_opened():
                print("СЕЙФ БЫЛ ОТКРЫТ!!!")
                await inter.response.edit_message(
                    embed=safe.get_embed(),
                    components=safe.get_components(correct=1),
                )
                opened_right_now = True
                content = open(
                    "databases/safe_content.txt", encoding="utf-8"
                ).read()
                await inter.followup.send(
                    f"Вы открыли сейф!　Никому не говорите, что внутри.\n"
                    f"Внутри сейфа было это послание:\n\n{content}",
                    ephemeral=True,
                )
                await inter.followup.send(
                    "Напишите сообщение в личные сообщения бота, "
                    "чтобы задать новое послание, "
                    "или сейф закроется с тем же посланием через пять минут.\n"
                    "Не забудьте написать ваше имя и дату!",
                    ephemeral=True,
                )
                try:
                    message = await self.bot.wait_for(
                        "message",
                        check=lambda x: isinstance(
                            x.channel, disnake.channel.DMChannel
                        )
                        and x.author == inter.author,
                        timeout=300,
                    )
                    with open(
                        "databases/safe_content.txt", "w", encoding="utf-8"
                    ) as file:
                        file.write(message.content.strip())
                    await inter.author.send(
                        "Послание оставлено! Теперь введите 3 цифры чтобы "
                        "задать новый пароль (или он останется старым)."
                    )
                except asyncio.TimeoutError:
                    print("таймаут сейфа")
                    opened_right_now = False
                    return
                while True:
                    try:
                        message = await self.bot.wait_for(
                            "message",
                            check=lambda x: (
                                x.channel == inter.author.dm_channel
                                and x.author == inter.author
                            ),
                            timeout=300,
                        )
                        password = message.content.strip()
                        if len(password) > 3:
                            password = password[:3]
                        if password.isdigit():
                            await inter.author.send(
                                "Новый пароль задан успешно. Операция закончена."
                            )
                            with open(
                                "databases/safe_password.txt",
                                "w",
                                encoding="utf-8",
                            ) as file:
                                file.write(password)
                                break
                        else:
                            await inter.author.dm_channel.send(
                                "Новый пароль некорректен. Введите его заново."
                            )
                    except asyncio.TimeoutError:
                        print("таймаут сейфа")
                        break
                opened_right_now = False
            else:
                print(f"{inter.author} attempt: {''.join(safe.numbers)}")
                safe.clear_numbers()
                await inter.response.edit_message(
                    embed=safe.get_embed(),
                    components=safe.get_components(correct=-1),
                )
        elif safe.numbers_are_full():
            await inter.response.edit_message()
        else:
            safe.insert_number(action)
            await inter.response.edit_message(
                embed=safe.get_embed(), components=safe.get_components()
            )


def setup(bot):
    bot.add_cog(SafeCog(bot))
