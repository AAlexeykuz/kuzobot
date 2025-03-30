import disnake
from disnake import ui
from disnake.ext import commands

off_emoji = "⚫"
on_emoji = "💡"
secondary = disnake.ButtonStyle.secondary
primary = disnake.ButtonStyle.primary
success = disnake.ButtonStyle.success
danger = disnake.ButtonStyle.danger
palette = {
    str(secondary): primary,
    str(primary): success,
    str(success): danger,
    str(danger): secondary,
}
invisible = "ㅤ"


class Switches(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="self-destruction", description="не нажимать")
    async def delete_button(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            components=[
                ui.Button(
                    label="удалить",
                    style=disnake.ButtonStyle.danger,
                    custom_id="delete",
                ),
            ],
        )

    @commands.slash_command(name="switch", description="переключатель")
    async def switch(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            components=[
                ui.Button(
                    label="off",
                    style=disnake.ButtonStyle.danger,
                    custom_id="off_switch",
                )
            ],
        )

    @commands.slash_command(name="lightbulbs", description="лампочки")
    async def row_of_switches(
        self, inter: disnake.ApplicationCommandInteraction, number_of_bulbs: int
    ):
        if not (1 <= number_of_bulbs <= 25):
            await inter.response.send_message("Некорректное число лампочек")
            return
        components = []
        for i in range(number_of_bulbs):
            components.append(
                ui.Button(
                    emoji=off_emoji,
                    style=secondary,
                    custom_id="bulb_switch" + str(i + 1),
                )
            )
        await inter.response.send_message(components=components)

    @commands.slash_command(name="canvas", description="рисовать")
    async def row_of_switches_painting(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        components = []
        for i in range(25):
            components.append(
                ui.Button(
                    label=invisible,
                    style=secondary,
                    custom_id="paint_switch" + str(i + 1),
                )
            )
        await inter.response.send_message(components=components)

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "delete":
            await inter.message.delete()
        elif "paint_switch" in inter.component.custom_id:
            number = inter.component.custom_id[12:]
            bulbs = []
            for i in inter.message.components:
                bulbs.extend(i.children)
            new_components = []
            for i in range(len(bulbs)):
                if i == int(number) - 1:
                    new_components.append(
                        ui.Button(
                            label=invisible,
                            style=palette[str(bulbs[i].style)],
                            custom_id="paint_switch" + str(i + 1),
                        )
                    )
                else:
                    new_components.append(
                        ui.Button(
                            label=invisible,
                            style=bulbs[i].style,
                            custom_id="paint_switch" + str(i + 1),
                        )
                    )
            print(f"[{inter.channel}] painting: {inter.author}")
            await inter.response.edit_message(components=new_components)
        elif "bulb_switch" in inter.component.custom_id:
            number = inter.component.custom_id[11:]
            bulbs = []
            for i in inter.message.components:
                bulbs.extend(i.children)
            new_components = []
            for i in range(len(bulbs)):
                if i == int(number) - 1:
                    if bulbs[i].style == primary:
                        new_components.append(
                            ui.Button(
                                emoji=off_emoji,
                                style=secondary,
                                custom_id="bulb_switch" + str(i + 1),
                            )
                        )
                    else:
                        new_components.append(
                            ui.Button(
                                emoji=on_emoji,
                                style=primary,
                                custom_id="bulb_switch" + str(i + 1),
                            )
                        )
                else:
                    new_components.append(
                        ui.Button(
                            emoji=bulbs[i].emoji,
                            style=bulbs[i].style,
                            custom_id="bulb_switch" + str(i + 1),
                        )
                    )
            print(f"[{inter.channel}] light bulb: {inter.author}")
            await inter.response.edit_message(components=new_components)
        if inter.component.custom_id in ["off_switch", "on_switch"]:
            if inter.component.custom_id == "off_switch":
                await inter.response.edit_message(
                    components=[
                        ui.Button(
                            label="on",
                            style=disnake.ButtonStyle.success,
                            custom_id="on_switch",
                        ),
                    ]
                )
            else:
                await inter.response.edit_message(
                    components=[
                        ui.Button(
                            label="off",
                            style=disnake.ButtonStyle.danger,
                            custom_id="off_switch",
                        ),
                    ]
                )


def setup(bot):
    bot.add_cog(Switches(bot))
