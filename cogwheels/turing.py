from time import sleep

import disnake
from disnake import ui
from disnake.ext import commands

EMPTY = "<:a:1283511031221456929>"
ZERO = ":zero:"
ONE = ":one:"
TAPE = ":heavy_minus_sign:"
MACHINE = ":fax:"
ID = "turing_"

saved_tapes = dict()
machine = 0


class Turing:
    def __init__(
        self,
        tape: str,
        program: str,
        position: int,
    ):
        self.error = None
        self.stop = False
        tape = self.compile_tape(tape)

        if tape is None:
            self.error = "Ошибка в ленте"
            return
        self.tape = tape

        program = self.compile_program(program)
        if program is None:
            return
        self.program = program
        self.state = next(iter(program.values()))
        self.state_name = list(self.program.keys())[0]
        self.position = position
        self.steps = 0

    def get_message(self) -> str:
        if self.error:
            return "```" + self.error + "```"
        length = 10
        output = TAPE * length + MACHINE + TAPE * length + "\n"
        for i in range(self.position - length, self.position + length + 1):
            if i in self.tape:
                value = self.tape[i]
                if value is None:
                    output += EMPTY
                elif value == 0:
                    output += ZERO
                else:
                    output += ONE
            else:
                output += EMPTY
        if self.stop:
            output += "\nПрограмма завершена успешно."
        output = f"Состояние: {self.state_name}\n" + output
        return output

    def compile_program(self, program: str):
        output = dict()

        lines = []
        line = ""
        nested = False
        count = 1

        for char in program:
            if char in "\n ":
                continue
            if char == "(":
                if nested:
                    self.error = f"Некорректные скобочки на строке {count}"
                    return None
                nested = True
            elif char == ")":
                if not nested:
                    self.error = f"Некорректные скобочки на строке {count}"
                    return None
                nested = False
            elif char == ";":
                lines.append(line)
                line = ""
                count += 1
                continue
            line += char
        lines.append(line)
        lines = [i for i in lines if i]
        if len(lines) == 0:
            self.error = (
                "Должно быть указано хотя-бы одно состояние для машины."
            )
            return None

        for i in range(len(lines)):
            line = lines[i].lower()
            if not (line.count("(") == 1 and line.count(")") == 1):
                self.error = (
                    f"Некорректные скобочки на строке {i + 1}. "
                    f'(Убедитесь, что разделили состояния ";")'
                )
                return None
            name, command = line.split("(")

            for char in "();,/=":
                if char in name:
                    self.error = (
                        f'Некорректное имя состояния "{name}" на строке {i + 1}'
                    )
                    return None
            if name in ["0", "1", "n", "r", "l", "stop"]:
                self.error = (
                    f'Некорректное имя состояния "{name}" на строке {i + 1}. '
                    f'Состояние не может быть названо "{name}", так как это ключевое слово.'
                )
                return None
            if name in output:
                self.error = (
                    f'Некорректное имя состояния "{name}" на строке {i + 1}. '
                    f"Такое состояние уже было объявлено."
                )
                return None
            if not name:
                self.error = (
                    f'Некорректное имя состояния "{name}" на строке {i + 1}'
                )
                return None

            command = command.replace(")", "")

            output_states = list()

            states = command.split("/")

            if len(states) != 3:
                self.error = (
                    f'Некорректное количество "/" внутри скобок на строке {i + 1}. '
                    f"(Должно быть ровно два)"
                )
                return None

            for j in range(len(states)):
                state = states[j]

                if j == 2:
                    value = None
                else:
                    value = j
                movement = 0
                next_state = name

                actions = state.split(",")

                length = len(actions)
                if length > 3:
                    self.error = (
                        f'Некорректное количество "," внутри скобок на строке {i + 1}. '
                        f"(Не может быть больше двух запятых в одном действии)"
                    )
                    return None
                if length == 1:
                    action = actions[0]
                    if action == "n":
                        value = None
                    elif action == "0":
                        value = 0
                    elif action == "1":
                        value = 1
                    elif action == "r":
                        movement = 1
                    elif action == "l":
                        movement = -1
                    elif action:
                        next_state = action
                    else:
                        next_state = "stop"
                elif length == 2:
                    action1, action2 = actions[0], actions[1]
                    if action1 in ["0", "1", "n"]:
                        if action1 == "n":
                            value = None
                        else:
                            value = int(action1)
                        if action2 == "r":
                            movement = 1
                        elif action2 == "l":
                            movement = -1
                        elif action2:
                            next_state = action2
                        else:
                            self.error = (
                                f"Пустое значение состояния на строке {i + 1}."
                            )
                            return None
                    elif action1 in ["r", "l"]:
                        if action1 == "r":
                            movement = 1
                        elif action1 == "l":
                            movement = -1
                        else:
                            self.error = f'Некорректное значение "{action1}" на строке {i + 1}.'
                            return None
                        if action2:
                            next_state = action2
                        else:
                            self.error = (
                                f"Пустое значение состояния на строке {i + 1}."
                            )
                            return None
                    else:
                        self.error = f'Некорректное значение "{action1}" на строке {i + 1}.'
                        return None
                else:
                    action1, action2, action3 = (
                        actions[0],
                        actions[1],
                        actions[2],
                    )
                    if action1 == "n":
                        value = None
                    elif action1 in ["0", "1"]:
                        value = int(action1)
                    else:
                        self.error = f'Некорректное значение "{action1}" на строке {i + 1}.'
                        return None
                    if action2 == "r":
                        movement = 1
                    elif action2 == "l":
                        movement = -1
                    else:
                        self.error = f'Некорректное значение "{action2}" на строке {i + 1}.'
                        return None
                    if action3:
                        next_state = action3
                    else:
                        self.error = (
                            f"Пустое значение состояния на строке {i + 1}."
                        )
                        return None
                output_states.append((value, movement, next_state))
            output[name] = tuple(output_states)
        return output

    @staticmethod
    def compile_tape(tape):
        if len(tape.replace("0", "").replace("1", "").replace(" ", "")) != 0:
            return None
        output = dict()
        for i in range(len(tape)):
            if tape[i] in "01":
                cell = int(tape[i])
            else:
                cell = None
            output[i] = cell
        return output

    def get_tape(self) -> str:
        output = ""
        numbers = self.tape.keys()
        start, end = min(numbers), max(numbers)
        for i in range(start, end + 1):
            if i in self.tape:
                value = self.tape[i]
                if value == 0:
                    output += "0"
                elif value == 1:
                    output += "1"
                else:
                    output += " "
            else:
                output += " "
        return output.strip()

    def step(self) -> bool:
        if self.error:
            return False
        self.steps += 1
        value = None
        if self.position in self.tape:
            value = self.tape[self.position]
        if value is None:
            value = 2
        set_value, movement, state_name = self.state[value]
        self.tape[self.position] = set_value
        self.position += movement
        if state_name.lower() == "stop":
            self.stop = True
            return False
        if state_name in self.program:
            self.state = self.program[state_name]
            self.state_name = state_name
            return True
        self.error = f"Ошибка во время выполнения на шаге {self.steps}: Состояния {state_name} не существует."
        return False


class TuringCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="turing", description="машинка тьюринга")
    async def turing(
        self,
        inter: disnake.ApplicationCommandInteraction,
        program: str,
        tape: str,
        speed: int = 1,
        step: int = 0,
        position: int = 0,
        from_right: bool = False,
    ):
        global machine
        if from_right:
            position += len(tape) - 1
        game = Turing(tape, program, position)

        await inter.response.send_message("Загрузка...", delete_after=0)
        message = await inter.channel.send(
            game.get_message(),
            components=[
                ui.Button(
                    label="Документация",
                    style=disnake.ButtonStyle.primary,
                    custom_id=ID + "documentation",
                )
            ],
        )
        count = 0
        machine = message.id
        while game.step():
            if message.id != machine:
                await message.delete()
                return
            count += 1
            if speed != 0 and count % speed == 0 and count > step:
                saved_tapes[message.id] = game.get_tape()
                if message.content != game.get_message() or True:
                    await message.edit(
                        game.get_message(),
                        components=[
                            ui.Button(
                                label="Просмотреть ленту",
                                custom_id=ID + "get_tape",
                            ),
                            ui.Button(
                                label="Документация",
                                style=disnake.ButtonStyle.primary,
                                custom_id=ID + "documentation",
                            ),
                        ],
                    )
                sleep(1)
            if count > 100000000:
                game.error = "Превышено максимальное количество шагов."
                break
        if message.id != machine:
            await message.delete()
            return
        saved_tapes[message.id] = game.get_tape()
        await message.edit(
            game.get_message(),
            components=[
                ui.Button(label="Посмотреть ленту", custom_id=ID + "get_tape"),
                ui.Button(
                    label="Документация",
                    style=disnake.ButtonStyle.primary,
                    custom_id=ID + "documentation",
                ),
            ],
        )

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith(ID):
            return
        action = inter.component.custom_id[len(ID) :]
        if action == "get_tape":
            if inter.message.id in saved_tapes:
                tape = saved_tapes[inter.message.id]
                await inter.response.send_message(
                    "```" + tape + "```", ephemeral=True
                )
            else:
                await inter.response.send_message(
                    "Полная лента больше не хранится в памяти бота.",
                    ephemeral=True,
                )
        elif action == "documentation":
            await inter.response.send_message(
                """
Машина Тьюринга (англ. Turing machine) — модель абстрактного вычислителя, предложенная британским математиком Аланом Тьюрингом в 1936 году.
Несмотря на свою простоту, на ней можно написать любой возможный алгоритм.
```/turing program tape (speed) (step) (position) (from right)```
- program - ваша программа. В ней указываются все состояния каретки. Состояния указываются так:
    ```Name(V,M,Q / V,M,Q / V,M,Q);```
    Name - название состояния. (Не может содержать символы "();,/=" и пробел, а так же не может быть "0", "1", "N", "R", "L" и "stop")
    Символом "/" отделяются действия каретки для нуля, единицы и пусто по порядку (для нуля / для единицы / для пусто).
    \n
    Сами действия состоят из трёх значений:
    V - значение, что каретка запишет в клеточку под ней. Принимает значения 0, 1, или N (пусто).
    M - куда передвинется каретка. Принимает значения R (направо) или L (налево).
    Q - название состояния, в которое каретка перейдёт после этого.
    Вы можете вписывать только те значения, которые изменятся, сохраняя место.
    \n
    Символ "/" **ставить два раза обязательно**, даже если между слэшами ничего нет.
    При переводе в состояние "stop" каретка прекращает работу.
    Несколько состояний обязательно нужно разделять точкой с запятой, потому что все символы пробела и новой строки удаляются при компиляции.
    Состояние, которое вы объявили первым, будет первоначальным состоянием каретки.
    
    
- tape (анг. лента) - строка, состоящая из нулей, единиц и пробелов. Набор символов, по которому будет двигаться каретка.
- speed - количество шагов в секунду (по умолчанию 1). Поставьте 0 для бесконечно быстрой машины.
- step - с какого количества шагов начать симуляцию (по умолчанию 0).
- position - местоположение каретки относительно изначального положения (по умолчанию 0).
- from_right - каретка начинает с правого конца ленты (по умолчанию false).

""",
                ephemeral=True,
                components=[
                    ui.Button(
                        label="Примеры программ",
                        style=disnake.ButtonStyle.primary,
                        custom_id=ID + "examples",
                    )
                ],
            )
        elif action == "examples":
            await inter.response.send_message(
                """
Примеры программ:
- Программа, прибавляющая к двоичному числу единицу:
```
Q1(R/R/L,Q2);
Q2(1,stop/0,L/1,stop);
```
- Программа, сортирующая нули и единицы двоичного числа:
```
Q1(L/L/R,Q2);
Q2(R/R,Q3/stop);
Q3(1,L,Q4/R/stop);
Q4(R,Q5/L/R,Q5);
Q5(/0,Q2/);
```
- Программа для сложения двух двоичных чисел, записанных через пробел:
```
q1(R/R/L,sub);
sub(1,L/0,q3/);
q3(R/R/R,q4);
q4(R/R/L,add);
add(1,q5/0,L/q5);
q5(L/L/L,sub);
```
""",
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(TuringCog(bot))
