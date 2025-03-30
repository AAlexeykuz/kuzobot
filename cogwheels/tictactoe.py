import disnake
from disnake import ui
from disnake.ext import commands

invisible = "ㅤ"
# def setup_database(conn):
#     """ create tables if they don't exist """
#     try:
#         cursor = conn.cursor()
#         cursor.execute('CREATE TABLE IF NOT EXISTS games (game TEXT, result INTEGER)')
#         cursor.execute('''CREATE TABLE IF NOT EXISTS count_table (id INTEGER PRIMARY KEY,
#                                                                   count INTEGER NOT NULL,
#                                                                   wins INTEGER NOT NULL,
#                                                                   draws INTEGER NOT NULL,
#                                                                   losses INTEGER NOT NULL);''')
#         cursor.execute('SELECT count FROM count_table')
#         if cursor.fetchone() is None:
#             cursor.execute('INSERT INTO count_table VALUES (1, 0, 0, 0, 0)')
#             cursor.execute('INSERT INTO count_table VALUES (2, 0, 0, 0, 0)')
#             conn.commit()
#     except sqlite3.Error as e:
#         print(e)

ID = "tic_tac_toe_"

active_games = dict()


class TicTacToe:
    def __init__(self, player1: disnake.Member, player2: disnake.Member):
        self.field = [None for _ in range(9)]
        self.sign = "x"
        self.draw = False
        self.current_player = player1
        self.other_player = player2

    def replace_winners(self, combination):
        for i in combination:
            if "0" in self.field[i]:
                self.field[i] = "0W"
            elif "x" in self.field[i]:
                self.field[i] = "xW"

    def is_game_over(self):
        combinations = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]
        for i in combinations:
            win = len({self.field[i[0]], self.field[i[1]], self.field[i[2]]})
            if win == 1 and self.field[i[0]] is not None:
                self.replace_winners(i)
                return True
        if all(self.field):
            self.draw = True
            return True
        return False

    def toggle_players(self):
        self.current_player, self.other_player = (
            self.other_player,
            self.current_player,
        )
        if self.sign == "x":
            self.sign = "0"
        else:
            self.sign = "x"

    def get_field(self):
        return self.field

    def get_player(self):
        return self.current_player

    def is_draw(self):
        return self.draw

    def is_singleplayer(self):
        if self.current_player == self.other_player:
            return True
        return False

    def make_move(self, move):
        if self.field[move] is None:
            self.field[move] = self.sign
            self.toggle_players()
            return True
        return False

    def to_components(self):
        buttons = []
        disabled = self.is_game_over()
        for i in range(9):
            if self.field[i] in ["0", "x", None]:
                style = disnake.ButtonStyle.secondary
            else:
                style = disnake.ButtonStyle.primary
            if self.field[i] is None:
                buttons.append(
                    ui.Button(
                        label=invisible,
                        style=style,
                        disabled=disabled,
                        custom_id="tic_tac_toe_" + str(i),
                    )
                )
            elif "0" in self.field[i]:
                buttons.append(
                    ui.Button(emoji="⭕", style=style, disabled=True)
                )
            elif "x" in self.field[i]:
                buttons.append(
                    ui.Button(emoji="❌", style=style, disabled=True)
                )
        components = [
            ui.ActionRow(*buttons[:3]),
            ui.ActionRow(*buttons[3:6]),
            ui.ActionRow(*buttons[6:]),
        ]
        return components


class TicTacToeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="tic-tac-toe", description="крестики-нолики")
    async def tic_tac_toe(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            f"Игра в крестики-нолики с {inter.author.mention}",
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
            game = TicTacToe(inter.author, inter.message.interaction.author)
            active_games[inter.message.id] = game
            if game.is_singleplayer() and False:
                await inter.response.send_message(
                    "Вы не можете играть сами с собой.", ephemeral=True
                )
                return
            await inter.message.edit(components=game.to_components())
            await inter.response.send_message(
                f"{inter.author.mention} присоединился и начинает! "
                f"{inter.message.interaction.author.mention}"
            )
        elif active_games[inter.message.id].get_player() == inter.author:
            game = active_games[inter.message.id]
            if not game.make_move(int(action)):
                await inter.response.send_message(
                    "Что-то пошло не так. Попробуйте ещё раз.", ephemeral=True
                )
                return
            await inter.response.edit_message(components=game.to_components())
            if game.is_game_over():
                del active_games[inter.message.id]
                if game.is_singleplayer():
                    return
                if game.is_draw():
                    await inter.followup.send("Ничья! Спасибо за игру.")
                else:
                    await inter.followup.send(
                        f"{inter.author.mention} победил! Спасибо за игру."
                    )
        else:
            await inter.response.send_message("Это не ваш ход.", ephemeral=True)


def setup(bot):
    bot.add_cog(TicTacToeCog(bot))
