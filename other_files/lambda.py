def find_calls(input_string):
    result = []
    stack = []
    i = 0
    while i < len(input_string):
        char = input_string[i]

        # Opening square bracket at first level
        if char == "[" and not stack:
            start_square = i
            i += 1
            while i < len(input_string) and (input_string[i] != "]" or stack):
                if input_string[i] == "[":
                    stack.append("[")
                elif input_string[i] == "]":
                    stack.pop()
                i += 1
            square_expr = input_string[start_square : i + 1]

            # Lookahead for circular bracket expression immediately following
            if i + 1 < len(input_string) and input_string[i + 1] == "(":
                start_circle = i + 1
                i += 2
                while i < len(input_string) and input_string[i] != ")":
                    i += 1
                circle_expr = input_string[start_circle : i + 1]
                result.append((square_expr, circle_expr))
            continue
        i += 1

    return result


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
        # print(code)
        called_functions = find_calls(code)
        # print(called_functions)
        for func_string, call in called_functions:
            func = Function(func_string)
            call_args = []
            output_calls = []
            for i in call[1:-1].split(","):
                if i.replace(".", "").isdigit():
                    call_args.append(float(i))
                else:
                    output_calls.append(i)
                    call_args.append("")
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


true = Function("[x,y:x]")
if_then = Function("[a,b:[x,y:x](a,b)]")
print(if_then(1))
