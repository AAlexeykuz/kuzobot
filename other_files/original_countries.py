from english_countries import ENG_COUNTRIES

COUNTRIES = {
    "а": [
        "абхазия",
        "австралия",
        "австрия",
        "азербайджан",
        "албания",
        "алжир",
        "ангола",
        "андорра",
        "антигуа и барбуда",
        "аргентина",
        "армения",
        "афганистан",
    ],
    "б": [
        "багамы",
        "бангладеш",
        "барбадос",
        "бахрейн",
        "белиз",
        "белоруссия",
        "бельгия",
        "бенин",
        "болгария",
        "боливия",
        "босния и герцеговина",
        "ботсвана",
        "бразилия",
        "бруней",
        "буркина-фасо",
        "бурунди",
        "бутан",
    ],
    "в": [
        "вануату",
        "ватикан",
        "великобритания",
        "венгрия",
        "венесуэла",
        "восточный тимор",
        "вьетнам",
    ],
    "г": [
        "габон",
        "гаити",
        "гайана",
        "гамбия",
        "гана",
        "гватемала",
        "гвинея",
        "гвинея-бисау",
        "германия",
        "гондурас",
        "гренада",
        "греция",
        "грузия",
    ],
    "д": ["дания", "джибути", "доминика", "доминикана", "др конго"],
    "е": ["египет"],
    "з": ["замбия", "зимбабве"],
    "и": [
        "израиль",
        "индия",
        "индонезия",
        "иордания",
        "ирак",
        "иран",
        "ирландия",
        "исландия",
        "испания",
        "италия",
    ],
    "й": ["йемен"],
    "к": [
        "кабо-верде",
        "казахстан",
        "камбоджа",
        "камерун",
        "канада",
        "катар",
        "кения",
        "кипр",
        "кирибати",
        "китай",
        "кндр",
        "колумбия",
        "коморы",
        "конго",
        "корея",
        "косово",
        "коста-рика",
        "кот-д’ивуар",
        "куба",
        "кувейт",
        "кыргызстан",
    ],
    "л": [
        "лаос",
        "латвия",
        "лесото",
        "либерия",
        "ливан",
        "ливия",
        "литва",
        "лихтенштейн",
        "люксембург",
    ],
    "м": [
        "маврикий",
        "мавритания",
        "мадагаскар",
        "малави",
        "малайзия",
        "мали",
        "мальдивы",
        "мальта",
        "марокко",
        "маршалловы острова",
        "мексика",
        "микронезия",
        "мозамбик",
        "молдавия",
        "монако",
        "монголия",
        "мьянма",
    ],
    "н": [
        "намибия",
        "науру",
        "непал",
        "нигер",
        "нигерия",
        "нидерланды",
        "никарагуа",
        "ниуэ",
        "новая зеландия",
        "норвегия",
    ],
    "о": ["оаэ", "оман", "острова кука"],
    "п": [
        "пакистан",
        "палау",
        "палестина",
        "панама",
        "папуа — новая гвинея",
        "парагвай",
        "перу",
        "пмр",
        "польша",
        "португалия",
    ],
    "р": ["россия", "руанда", "румыния"],
    "с": [
        "садр",
        "сальвадор",
        "самоа",
        "сан-марино",
        "сан-томе и принсипи",
        "саудовская аравия",
        "северная македония",
        "сейшелы",
        "сенегал",
        "сент-винсент и гренадины",
        "сент-китс и невис",
        "сент-люсия",
        "сербия",
        "сингапур",
        "сирия",
        "словакия",
        "словения",
        "соломоновы острова",
        "сомали",
        "судан",
        "суринам",
        "сша",
        "сьерра-леоне",
        "сомалиленд",
    ],
    "т": [
        "таджикистан",
        "таиланд",
        "тайвань",
        "танзания",
        "того",
        "тонга",
        "тринидад и тобаго",
        "трск",
        "тувалу",
        "тунис",
        "туркменистан",
        "турция",
    ],
    "у": ["уганда", "узбекистан", "украина", "уругвай"],
    "ф": ["фиджи", "филиппины", "финляндия", "франция"],
    "х": ["хорватия"],
    "ц": ["цар"],
    "ч": ["чад", "черногория", "чехия", "чили"],
    "ш": ["швейцария", "швеция", "шри-ланка"],
    "э": [
        "эквадор",
        "экваториальная гвинея",
        "эритрея",
        "эсватини",
        "эстония",
        "эфиопия",
    ],
    "ю": ["юар", "южная осетия", "южный судан"],
    "я": ["ямайка", "япония"],
}
EXCEPTIONS = [
    "япония",
    "восточный тимор",
    "катар",
    "кипр",
    "кндр",
    "коморы",
    "кот-д’ивуар",
    "мадагаскар",
    "нигер",
    "пмр",
    "садр",
    "сальвадор",
    "сингапур",
    "цар",
    "эквадор",
    "юар",
    "norway",
]
MAX_DEPTH = 11


def get_letter(country):
    if country[-1] in "ьыъ":
        letter = country[-2]
    else:
        letter = country[-1]
    return letter


def check_country(country, letter, countries):
    if letter is not None and country[0] != letter:
        print("Вы назвали страну с неправильной буквы.")
        return False
    if letter is None and country in EXCEPTIONS:
        print(f"Нельзя выбрать {country.capitalize()} первой страной.")
        return False
    if country in countries[country[0]]:
        return True
    print(
        "Вы ошиблись в названии страны или такая страна уже названа. Бот использует этот источник:\n"
        "https://ru.wikipedia.org/wiki/Список_государств"
    )
    return False


# def calculate_score(country, countries, depth):
#     countries[country[0]].remove(country)
#     player = depth % 2
#     possible_countries = tuple(countries[get_letter(country)])
#     if not possible_countries:
#         countries[country[0]].append(country)
#         if player == 0:
#             # print(depth, '\t' * depth, player, country, 'ПОБЕДА')
#             return MAX_DEPTH * 3 + 1 + depth
#         else:
#             # print(depth, '\t' * depth, player, country, 'ПОРАЖЕНИЕ')
#             return -(MAX_DEPTH * 3 + 1 + depth)
#     if depth == MAX_DEPTH:
#         countries[country[0]].append(country)
#         return depth
#     results = []
#     for i in possible_countries:
#         result = calculate_score(i, countries, depth + 1)
#         # if depth == 0:
#         #     results.append((result, i))
#         # else:
#         #     results.append(result)
#         results.append(result)
#     # print(depth, '\t' * depth, player, country, results)
#     countries[country[0]].append(country)
#     if player:
#         return max(results)
#     else:
#         return min(results)


# chatgpt's version
def calculate_score(
    country, countries, depth, alpha=float("-inf"), beta=float("inf")
):
    countries[country[0]].remove(country)
    player = depth % 2
    possible_countries = tuple(countries[get_letter(country)])

    if not possible_countries:
        countries[country[0]].append(country)
        if player == 0:
            return MAX_DEPTH * 2 + 1 - depth
        return -(MAX_DEPTH * 2 + 1 - depth)

    if depth == MAX_DEPTH:
        countries[country[0]].append(country)
        return depth

    if player != 0:
        value = float("-inf")
        for i in possible_countries:
            value = max(
                value, calculate_score(i, countries, depth + 1, alpha, beta)
            )
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # beta cut-off
    else:
        value = float("inf")
        for i in possible_countries:
            value = min(
                value, calculate_score(i, countries, depth + 1, alpha, beta)
            )
            beta = min(beta, value)
            if beta <= alpha:
                break  # alpha cut-off

    countries[country[0]].append(country)
    return value


def calculate_next_country(country, countries):
    countries[country[0]].remove(country)
    possible_countries = tuple(countries[get_letter(country)])
    if not possible_countries:
        print("Сдаюсь")
        return None
    choices = []
    for c in possible_countries:
        score = calculate_score(c, countries, 0)
        choices.append((score, c))
    choices.sort()
    # print(f'Evaluation: {choices[-1][0]}')
    countries[choices[-1][1][0]].remove(choices[-1][1])
    return choices[-1][1]


def eng_game():
    countries = {}
    for i in ENG_COUNTRIES:
        countries[i] = ENG_COUNTRIES[i][:]
    letter = None
    print("Name a country first.")
    while True:
        if letter is not None:
            if not len(countries[get_letter(output_country)]):
                print("Game over.")
                break
        country = input().lower()
        check = check_country(country, letter, countries)
        while not check:
            country = input().lower()
            check = check_country(country, letter, countries)
        output_country = calculate_next_country(country, countries)
        if output_country is None:
            break
        letter = get_letter(output_country)
        print(f"My country: {output_country.capitalize()}.")


def ru_game():
    countries = {}
    for i in COUNTRIES:
        countries[i] = COUNTRIES[i][:]
    letter = None
    print("Начинайте игру.")
    while True:
        if letter is not None:
            if not len(countries[get_letter(output_country)]):
                print("Вы проиграли.")
                break
        country = input().lower()
        check = check_country(country, letter, countries)
        while not check:
            country = input().lower()
            check = check_country(country, letter, countries)
        output_country = calculate_next_country(country, countries)
        if output_country is None:
            break
        letter = get_letter(output_country)
        print(f"Моя страна - {output_country.capitalize()}.")


ru_game()
