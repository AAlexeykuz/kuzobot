from constants import GUILD_IDS
import disnake
from disnake.ext import commands
from disnake import ui
from numba import cuda
from PIL import Image
import time
from io import BytesIO
import cupy as cp
import math

ID = "fractals_"
BLUE = disnake.ButtonStyle.primary
GRAY = disnake.ButtonStyle.secondary
GREEN = disnake.ButtonStyle.success
RED = disnake.ButtonStyle.danger
active_fractals = dict()


class Fractal:
    def __init__(self,
                 title,
                 point,
                 scale,
                 max_iterations,
                 color_scheme=((0, 0, 0), (255, 255, 255), (255, 255, 255))
                 ):
        buttons = [ui.Button(emoji="↖️", custom_id=ID + "left_up", style=BLUE),
                   ui.Button(emoji="⬆️", custom_id=ID + "up", style=BLUE),
                   ui.Button(emoji="↗️", custom_id=ID + "right_up", style=BLUE),
                   ui.Button(label="2x", custom_id=ID + "zoom+2", style=GREEN),
                   ui.Button(label="0.5x", custom_id=ID + "zoom-2", style=RED),
                   ui.Button(emoji="⬅️", custom_id=ID + "left", style=BLUE),
                   ui.Button(emoji="⚫", custom_id=ID + "mid", style=GRAY, disabled=True),
                   ui.Button(emoji="➡️", custom_id=ID + "right", style=BLUE),
                   ui.Button(label="4x", custom_id=ID + "zoom+4", style=GREEN),
                   ui.Button(label="0.25x", custom_id=ID + "zoom-4", style=RED),
                   ui.Button(emoji="↙️", custom_id=ID + "left_down", style=BLUE),
                   ui.Button(emoji="⬇️", custom_id=ID + "down", style=BLUE),
                   ui.Button(emoji="↘️", custom_id=ID + "right_down", style=BLUE),
                   ui.Button(label="📏📈", custom_id=ID + "+iterations", style=GREEN),
                   ui.Button(label="📏📉", custom_id=ID + "-iterations", style=RED),
                   ]
        self.components = [ui.ActionRow(*buttons[:5]),
                           ui.ActionRow(*buttons[5:10]),
                           ui.ActionRow(*buttons[10:])]
        self.point = list(point)
        self.scale = scale
        self.set_color = cp.array(color_scheme[-1], dtype=cp.uint8)
        self.color_scheme = [cp.array(color, dtype=cp.uint8) for color in color_scheme[:-1]]
        self.max_iterations = max_iterations
        self.resolution = 512
        self.generating_time = None
        self.title = title

    def handle_action(self, action):
        if action == "zoom+2":
            self.scale /= 2
        elif action == "zoom+4":
            self.scale /= 4
        elif action == "zoom-2":
            self.scale *= 2
        elif action == "zoom-4":
            self.scale *= 4
        elif action == "+iterations" and self.max_iterations < 2 ** 18:
            self.max_iterations *= 2
        elif action == "-iterations" and self.max_iterations > 1:
            self.max_iterations //= 2

        if "left" in action:
            self.point[0] -= self.scale / 2
        elif "right" in action:
            self.point[0] += self.scale / 2
        if "up" in action:
            self.point[1] -= self.scale / 2
        elif "down" in action:
            self.point[1] += self.scale / 2

    def generate_image_file(self):
        start_time = time.time()

        # Define the range for the real and imaginary parts
        start_x, start_y = self.point[0] - self.scale, self.point[1] - self.scale
        end_x, end_y = self.point[0] + self.scale, self.point[1] + self.scale

        # Generate the grid on the GPU
        x = cp.linspace(start_x, end_x, self.resolution)
        y = cp.linspace(start_y, end_y, self.resolution)
        real, imag = cp.meshgrid(x, y)

        # Compute Mandelbrot escape times on the GPU
        max_iterations = self.max_iterations
        self.max_iterations = max_iterations

        stream = cp.cuda.Stream(non_blocking=True)  # я не знаю что делает эта штука, но она повышала производительность
        # примерно на 20% в прошлых тестах поэтому я её оставил
        with stream:
            iterations = self.function(real, imag, max_iterations=max_iterations)
        stream.synchronize()
        # Normalize iterations for coloring
        normalized = (iterations / max_iterations) ** 0.6

        # Generate pixel data
        pixels = cp.zeros((self.resolution, self.resolution, 3), dtype=cp.uint8)

        # Use vectorized approach for coloring
        mandelbrot_mask = iterations == max_iterations
        pixels[mandelbrot_mask] = self.set_color  # Mandelbrot set points
        color_values = self.interpolate_color(normalized[~mandelbrot_mask])
        pixels[~mandelbrot_mask] = color_values
        # Convert pixels to numpy for image creation
        pixels = cp.asnumpy(pixels)

        bytes_io = BytesIO()
        Image.fromarray(pixels, mode="RGB").save(bytes_io, format="PNG")
        bytes_io.seek(0)
        file = disnake.File(bytes_io, filename="fractal.png")
        self.generating_time = time.time() - start_time
        return file

    def get_text(self) -> str:
        return (
            f"## {self.title}\n"
            f"Генерация заняла {self.generating_time:.2F}с\n"
            f"X:\t{self.point[0]}\n"
            f"Y:\t{self.point[1]}\n"
            f"Приближение:\t2^{-round(math.log2(self.scale))}\n"
            f"Точность:\t{self.max_iterations}")

    def get_message_kwargs(self) -> dict:
        output = dict()
        output["file"] = self.generate_image_file()
        output["content"] = self.get_text()
        output["components"] = self.components
        return output

    def function(self, real, imag, max_iterations):  # Пустышка
        pass

    def interpolate_color(self, value):
        value = cp.clip(value, 0, 1)
        color_indices = (value * (len(self.color_scheme) - 1)).astype(cp.int32)
        segment_value = (value * (len(self.color_scheme) - 1)) - color_indices
        start_colors = cp.stack([self.color_scheme[i] for i in range(len(self.color_scheme) - 1)])
        end_colors = cp.stack([self.color_scheme[i + 1] for i in range(len(self.color_scheme) - 1)])
        start_color = start_colors[color_indices]
        end_color = end_colors[color_indices]
        result = start_color + segment_value[..., None] * (end_color - start_color)
        return cp.clip(result, 0, 255).astype(cp.uint8)


class MandelbrotSet(Fractal):
    @staticmethod
    @cuda.jit
    def mandelbrot_kernel(real, imag, max_iters, result):
        """
        CUDA kernel to compute Mandelbrot escape times.
        This will run on the GPU.
        """
        i, j = cuda.grid(2)
        if i < result.shape[0] and j < result.shape[1]:
            x = real[i, j]
            y = imag[i, j]
            zx, zy = x, y
            iteration = 0
            while iteration < max_iters and zx * zx + zy * zy <= 4.0:
                tmp = zx * zx - zy * zy + x
                zy, zx = 2.0 * zx * zy + y, tmp
                iteration += 1
            result[i, j] = iteration

    def function(self, real, imag, max_iterations):
        """
        Computes the Mandelbrot set escape times using the GPU kernel.
        """
        # Create an array to store results
        result = cp.zeros((self.resolution, self.resolution), dtype=cp.int32)

        # Define CUDA grid and block dimensions
        threads_per_block = (16, 16)
        blocks_per_grid = (int((real.shape[0] + threads_per_block[0] - 1) / threads_per_block[0]),
                           int((real.shape[1] + threads_per_block[1] - 1) / threads_per_block[1]))

        # Launch kernel
        self.mandelbrot_kernel[blocks_per_grid, threads_per_block](real, imag, max_iterations, result)

        return result


def hex_to_rgb(hex_code: str) -> tuple:
    hex_code = hex_code.lstrip('#')
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    return r, g, b


class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="mandelbrot", description="посетите множество Мандельброта", guild_ids=GUILD_IDS)
    async def mandelbrot(self,
                         inter: disnake.ApplicationCommandInteraction,
                         x: float = -1,
                         y: float = 0,
                         zoom: float = 0.5,
                         ):
        await inter.response.defer()
        global active_fractals
        point = x, y
        scale = 1 / zoom
        color_scheme = (hex_to_rgb("31222b"), hex_to_rgb("fff075"), (0, 0, 0))
        mandelbrot_set = MandelbrotSet("Множество Мандельброта",
                                       point,
                                       scale,
                                       512,
                                       color_scheme)
        message = await inter.followup.send(**mandelbrot_set.get_message_kwargs())
        active_fractals[message.id] = mandelbrot_set

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith(ID):
            return
        if inter.message.id not in active_fractals:
            await inter.response.send_message("Это окно уже не работает, активируйте новое с помощью /mandelbrot",
                                              ephemeral=True)
            return
        await inter.response.defer()
        action = inter.component.custom_id[len(ID):]
        print(f"Фракталы: {inter.author.name} - {action}")
        fractal = active_fractals[inter.message.id]
        fractal.handle_action(action)
        image_file = fractal.generate_image_file()
        inter.message.attachments = []
        await inter.followup.edit_message(message_id=inter.message.id,
                                          file=image_file,
                                          attachments=[],
                                          content=fractal.get_text(),
                                          )

def setup(bot):
    bot.add_cog(Cog(bot))
