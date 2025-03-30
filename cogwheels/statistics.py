import datetime
from datetime import timedelta

import disnake
import matplotlib.pyplot as plt
from disnake.ext import commands


class StatisticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="statistics", description="статистика канала")
    async def statistics(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.channel.TextChannel,
        days: int = 14,
    ):
        await inter.response.defer()
        if days < 1:
            await inter.response.send_message("Некорректное количество дней")
            return

        today = datetime.date.today()
        end = today - timedelta(days=days)
        last_date = today

        this_day = 0
        all_days = []
        messages_count = dict()
        stop_flag = False

        async for message in channel.history(limit=1000000):
            date = message.created_at.date()
            while last_date != date:
                last_date -= timedelta(days=1)
                all_days.insert(0, this_day)
                this_day = 0
                if last_date <= end:
                    stop_flag = True
                    break
            if stop_flag:
                break
            if message.author.name in messages_count:
                messages_count[message.author.name] += 1
            else:
                messages_count[message.author.name] = 1
            this_day += 1

        most_active_users = sorted(
            messages_count.items(), key=lambda item: item[1], reverse=True
        )
        if len(most_active_users) > 10:
            most_active_users = most_active_users[:10]
        most_active_users = [f"{i[0]}: {i[1]}" for i in most_active_users]
        if len(most_active_users) > 0:
            most_active_users[0] += " :first_place:"
        if len(most_active_users) > 1:
            most_active_users[1] += " :second_place:"
        if len(most_active_users) > 2:
            most_active_users[2] += " :third_place:"

        plt.bar(list(range(1, len(all_days) + 1)), all_days)
        plt.ylabel("Сообщений в день")
        plt.xlabel(f"Дней: {len(all_days)}")
        plt.savefig(f"generated_images/{inter.author.id}.png")
        plt.close()

        embed = disnake.Embed(
            title="Статистика",
            description=f"Канал #{channel.name}."
            f"\nСообщений: {sum(all_days)}"
            f"\nСредняя скорость: {round(sum(all_days) / len(all_days), 3)} сообщений / день",
        )
        embed.add_field(
            name="Самые активные пользователи",
            value="\n".join(most_active_users),
        )
        embed.set_image(
            file=disnake.File(f"generated_images/{inter.author.id}.png")
        )
        await inter.followup.send(embed=embed)


def setup(bot):
    bot.add_cog(StatisticsCog(bot))
