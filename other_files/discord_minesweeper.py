from random import sample

BOMB = ":boom:"
NUMBERS = [
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

# DIFFICULTY_RATIOS = {
#     'easy': 0.101,
#     'normal': 0.15625,
#     'hard': 0.20625,
#     'extreme': 0.25
# }
#
#
# def calculate_bombs(difficulty, size):
#     return round(size * DIFFICULTY_RATIOS[difficulty])


def generate_field(side_x, side_y, bombs):
    bomb_coords = set(sample(range(side_x * side_y), bombs))

    field = [
        "||"
        + (
            BOMB
            if index in bomb_coords
            else NUMBERS[
                sum(
                    (nx + ny * side_x) in bomb_coords
                    for nx in range(max(0, x - 1), min(side_x, x + 2))
                    for ny in range(max(0, y - 1), min(side_y, y + 2))
                    if nx != x or ny != y
                )
            ]
        )
        + "||"
        for y in range(side_y)
        for x in range(side_x)
        for index in [y * side_x + x]
    ]

    return [
        "".join(field[i * side_x : (i + 1) * side_x]) for i in range(side_y)
    ]


print("\n".join(generate_field(16, 6, 15)))
