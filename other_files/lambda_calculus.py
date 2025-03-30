import re
import sys
import threading

import disnake
from disnake.ext import commands


def quit_function(fn_name):
    print(f"{fn_name} took too long", file=sys.stderr)
    sys.stderr.flush()
    thread.interrupt_main()


def exit_after(s):
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result

        return inner

    return outer


def find_calls(s):
    output = []
    depth = 0
    in_square = False
    in_circle = False
    square_expr = ""
    circular_expr = ""
    for i in range(len(s)):
        char = s[i]
        if char == "[":
            if depth == 0:
                in_square = True
                if square_expr and circular_expr:
                    output.append(
                        (square_expr, circular_expr.replace(")(", ","))
                    )
                square_expr = ""
                circular_expr = ""
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                square_expr += char
                in_square = False
        elif char == "(":
            if depth == 0:
                in_circle = True
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                circular_expr += char
                in_circle = False
        if depth:
            if in_square:
                square_expr += char
            elif in_circle:
                circular_expr += char
    if square_expr and circular_expr:
        output.append((square_expr, circular_expr.replace(")(", ",")))
    return output


def split_preserving_brackets(input_string):
    pattern = r"\[.*?\]|\(.*?\)|[^,\[\]()]+"
    parts = re.findall(pattern, input_string)
    return parts


def parse_function_call(input_string):
    open_parenthesis_index = input_string.find("(")
    function_name = input_string[:open_parenthesis_index].strip()
    arguments_string = input_string[open_parenthesis_index + 1 : -1]
    arguments = [
        arg.strip() for arg in split_preserving_brackets(arguments_string)
    ]
    return function_name, arguments


class Function:
    def __init__(self, func: str):
        func = func[1:-1]
        args, actions = func.split(":", 1)
        self.variables = []
        for arg in args.split(","):
            self.variables.append(arg)
        self.actions = actions

    def __str__(self):
        output = "[" + ",".join(self.variables) + ":" + self.actions + "]"
        return output

    def __call__(self, *args):
        code = self.actions
        new_code = [""]
        for char in code:
            if char == "[":
                new_code.append("")
                new_code[-1] += char
            elif char == "]":
                new_code[-1] += char
                new_code.append("")
            else:
                new_code[-1] += char
        for i in range(len(new_code)):
            s = new_code[i]
            if "[" not in s and "]" not in s:
                for j in range(len(args)):
                    if args[j] == "":
                        continue
                    new_code[i] = new_code[i].replace(
                        self.variables[j], str(args[j])
                    )
        variables = []
        for i in range(len(args)):
            if args[i] == "":
                variables.append(self.variables[i])
        variables.extend(self.variables[len(args) :])
        args = [i for i in args if i != ""]
        code = "".join(new_code)
        # print("code", code)
        called_functions = find_calls(code)
        # print(called_functions)
        for func_string, call in called_functions:
            func = Function(func_string)
            call_args = []
            output_calls = []
            for i in split_preserving_brackets(call[1:-1]):
                if i.replace(".", "").isdigit():
                    call_args.append(float(i))
                elif i[0] != "[":
                    call_args.append(i)
                else:
                    call_args.append(Function(i))
            func = func(*call_args)
            replace_calls = ""
            if output_calls:
                replace_calls = "(" + ",".join(output_calls) + ")"
            if func_string + call in code:
                code = code.replace(
                    func_string + call, str(func) + replace_calls
                )
        temp = code
        for i in ["+", "-", "*", "/", "%", ".", "(", ")"]:
            temp = temp.replace(i, "")
        if len([i for i in args if i != ""]) < len(self.variables):
            func = "[" + ",".join(variables) + ":" + code + "]"
            return Function(func)
        if temp.isdigit():
            return eval(compile(code, "", "eval"))
        return Function(code)


class LambdaCompiler:
    def __init__(self):
        self.output = "Вывод:\n```\n"
        self.variables = {
            "true": Function("[x,y:x]"),
            "false": Function("[x,y:y]"),
        }
        self.special_methods = {
            "print": self.print,
            "see": self.see,
            "unicode": self.char,
        }

    def get_output(self):
        if len(self.output) < 500:
            return self.output + "```"
        return self.output[:500] + f"\nЕщё {len(self.output) - 500}...```"

    # @exit_after(10)
    def compile(self, code):
        code = code.replace("->", "").replace("^", "**")
        for char in [" ", "\n", "\t"]:
            code = code.replace(char, "")
        lines = code.split(";")
        next_lines = ""
        if len(lines) > 19:
            next_lines = f"\n{len(lines) - 19}..."
        self.output = (
            "Исполняю код:```"
            + ";\n".join(lines[:20])
            + next_lines
            + "```"
            + self.output
        )
        for i in range(len(lines)):
            line = lines[i]
            if not line:
                continue
            if line.count("=") > 1:
                self.output += (
                    f"\nОшибка на строке {i}: Более одного оператора присваивания в одной строке - "
                    f"{line}"
                )
                return
            if "=" in line:
                name, code = line.split("=")
            else:
                name, code = "", line
            # delimiters = ["(", ")", ",", ":"]
            # string = " ".join(split_preserving_brackets(code))
            # for delimiter in delimiters:
            #     string = " ".join(string.split(delimiter))
            # print(string.split())
            # for j in string.split():
            #     if j.isdigit():
            #         continue
            #     elif "[" in j:
            #         continue
            #     elif j not in self.variables and j not in self.special_methods:
            #         self.output += (f"\nОшибка на строке {i + 1}: Неизвестная переменная - "
            #                         f"{line}")
            #         return
            print("до", code)
            code = self.safe_replace_variables(code)
            print("после", code)
            find_code = code
            for key in self.special_methods:
                if code.startswith(key):
                    find_code = code[len(key) + 1 : -1]
                    break
            print(find_code)
            called_functions = find_calls(find_code)
            print(called_functions)
            for func_string, call in called_functions:
                func = Function(func_string)
                call_args = []
                for j in split_preserving_brackets(call[1:-1]):
                    if j.replace(".", "").isdigit():
                        call_args.append(float(j))
                    else:
                        try:
                            call_args.append(Function(j))
                        except Exception as error:
                            print("lambda calculus error 1:", error)
                            self.output += f"\nОшибка на строке {i + 1}: Неизвестный аргумент - {j}"
                            return
                try:
                    func = func(*call_args)
                except Exception as error:
                    print("lambda calculus error 2:", error)
                    if type(error) is RecursionError:
                        self.output += (
                            f"\nОшибка на строке {i + 1}: Достигнута максимальная глубина рекурсии - "
                            f"{line}"
                        )
                    else:
                        self.output += (
                            f"\nОшибка на строке {i + 1}: Некорректный вызов функции - {line}"
                            f"(Возможно, функция была объявлена неправильно изначально)"
                        )
                    return
                if func_string + call in code:
                    code = code.replace(func_string + call, str(func))
            print(code)
            if name:
                if ":" in code:
                    try:
                        self.variables[name] = Function(code)
                        continue
                    except Exception as error:
                        print("lambda calculus error 3:", error)
                        self.output += f"\nОшибка на строке {i + 1}: Некорректное объявление функции - {code}"
                        return
                else:
                    self.output += f"\nОшибка на строке {i + 1}: Неизвестная переменная - {code}"
                    return
            else:
                name, arguments = parse_function_call(code)
                if name not in self.special_methods:
                    self.output += f"\nОшибка на строке {i + 1}: Неизвестная функция - '{name}'"
                    return
                try:
                    self.special_methods[name](*arguments)
                except ValueError as error:
                    print("lambda calculus error 4:", error)
                    self.output += f"\nОшибка на строке {i + 1}: Некорректный вызов функции - '{code}'\n"
                    return

    def safe_replace_variables(self, code_line):
        pattern = r"\b(?<!\$\d)\w+\b"
        bracket_content = {}
        placeholder_index = 0

        def exclude_brackets(match):
            nonlocal placeholder_index
            lambda_placeholder = f"__PLACEHOLDER{placeholder_index}__"
            bracket_content[lambda_placeholder] = match.group(0)
            placeholder_index += 1
            return lambda_placeholder

        code_line = re.sub(r"\[.*?]", exclude_brackets, code_line)

        def replace_match(match):
            word = match.group(0)
            if word in self.variables:
                return f"${self.variables[word]}$"
            if word.isdigit():
                try:
                    number = int(word)
                    return f"${'[f,x:' + 'f(' * number + 'x' + ')' * number + ']'}$"
                except MemoryError:
                    self.output += (
                        f"\nОшибка на строке {i}: Перегрузка памяти {line}"
                    )
            return word

        replaced_line = re.sub(pattern, replace_match, code_line)
        final_line = replaced_line.replace("$", "")
        for placeholder, original_content in bracket_content.items():
            final_line = final_line.replace(placeholder, original_content)

        return final_line

    def print(self, *args):
        print(args)
        for i in args:
            result = i
            if "f(" in i and i.count(")") == i.count("f("):
                print(")".join(i.split("(")).split(")"))
                number = 0
                for j in ")".join(i.split("(")).split(")"):
                    print(j)
                    if number == 0 and j == "[f,x:f":
                        number = 1
                    elif number == 1 and j in ["f", "x"]:
                        if j == "x":
                            number = 2
                    elif number == 2 and j in ["", "]"]:
                        if j == "]":
                            result = str(i.count("f("))
                    else:
                        break
            self.output += result + "\n"

    def see(self, *args):
        for i in args:
            self.output += str(i) + "\n"

    def char(self, *args):
        for i in args:
            self.output += chr(int(i))


class LambdaCalculusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.slash_command(name='лямбда',
    #                         description='страшный язык программирования.'
    #                                     ' Пародия на лямбда калькулюс')
    async def lambda_calculus(
        self, inter: disnake.ApplicationCommandInteraction, code: str
    ):
        await inter.response.defer()
        compiler = LambdaCompiler()
        compiler.compile(code)
        await inter.followup.send(compiler.get_output())


def setup(bot):
    bot.add_cog(LambdaCalculusCog(bot))
