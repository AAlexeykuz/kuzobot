import asyncio
import sqlite3
from random import choice

import disnake
from disnake.ext import commands

from constants import GUILD_IDS
from database import create_connection

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
ENG_COUNTRIES = {
    "a": [
        "afghanistan",
        "albania",
        "algeria",
        "andorra",
        "angola",
        "antigua and barbuda",
        "argentina",
        "armenia",
        "australia",
        "austria",
        "azerbaijan",
        "abkhazia",
    ],
    "b": [
        "bahamas",
        "bahrain",
        "bangladesh",
        "barbados",
        "belarus",
        "belgium",
        "belize",
        "benin",
        "bhutan",
        "bolivia",
        "bosnia and herzegovina",
        "botswana",
        "brazil",
        "brunei",
        "bulgaria",
        "burkina faso",
        "burundi",
    ],
    "c": [
        "cambodia",
        "cameroon",
        "canada",
        "cape verde",
        "central african republic",
        "chad",
        "chile",
        "china",
        "colombia",
        "comoros",
        "costa rica",
        "croatia",
        "cuba",
        "cyprus",
        "czech republic",
        "cook islands",
    ],
    "h": ["hong kong", "haiti", "honduras", "hungary"],
    "m": [
        "macao",
        "madagascar",
        "malawi",
        "malaysia",
        "maldives",
        "mali",
        "malta",
        "marshall islands",
        "mauritania",
        "mauritius",
        "mexico",
        "micronesia",
        "moldova",
        "monaco",
        "mongolia",
        "montenegro",
        "morocco",
        "mozambique",
        "myanmar",
    ],
    "d": [
        "democratic republic of the congo",
        "denmark",
        "djibouti",
        "dominica",
        "dominican republic",
    ],
    "r": ["republic of the congo", "romania", "russia", "rwanda"],
    "f": ["faroe islands", "fiji", "finland", "france"],
    "g": [
        "greenland",
        "gabon",
        "gambia",
        "georgia",
        "germany",
        "ghana",
        "greece",
        "grenada",
        "guatemala",
        "guinea",
        "guinea-bissau",
        "guyana",
    ],
    "e": [
        "east timor",
        "ecuador",
        "egypt",
        "el salvador",
        "equatorial guinea",
        "eritrea",
        "estonia",
        "eswatini",
        "ethiopia",
    ],
    "i": [
        "iceland",
        "india",
        "indonesia",
        "iran",
        "iraq",
        "ireland",
        "israel",
        "italy",
        "ivory coast",
    ],
    "j": ["jamaica", "japan", "jordan"],
    "k": ["kazakhstan", "kenya", "kiribati", "kuwait", "kyrgyzstan"],
    "l": [
        "laos",
        "latvia",
        "lebanon",
        "lesotho",
        "liberia",
        "libya",
        "liechtenstein",
        "lithuania",
        "luxembourg",
    ],
    "n": [
        "namibia",
        "nauru",
        "nepal",
        "netherlands",
        "new zealand",
        "niue",
        "nicaragua",
        "niger",
        "nigeria",
        "north korea",
        "north macedonia",
        "norway",
        "northern cyprus",
    ],
    "o": ["oman"],
    "p": [
        "pakistan",
        "palau",
        "palestine",
        "panama",
        "papua new guinea",
        "paraguay",
        "peru",
        "philippines",
        "poland",
        "portugal",
    ],
    "q": ["qatar"],
    "s": [
        "saint kitts and nevis",
        "saint lucia",
        "saint vincent and the grenadines",
        "samoa",
        "san marino",
        "sao tome and principe",
        "saudi arabia",
        "senegal",
        "serbia",
        "seychelles",
        "sierra leone",
        "singapore",
        "slovakia",
        "slovenia",
        "solomon islands",
        "somalia",
        "south africa",
        "south korea",
        "south sudan",
        "spain",
        "sri lanka",
        "sudan",
        "suriname",
        "sweden",
        "switzerland",
        "syria",
        "sahrawi arab democratic republic",
        "somaliland",
        "south ossetia",
    ],
    "t": [
        "tajikistan",
        "tanzania",
        "thailand",
        "togo",
        "tonga",
        "trinidad and tobago",
        "tunisia",
        "turkey",
        "turkmenistan",
        "tuvalu",
        "taiwan",
        "transnistria",
    ],
    "u": [
        "uganda",
        "ukraine",
        "united arab emirates",
        "united kingdom",
        "united states",
        "uruguay",
        "uzbekistan",
    ],
    "v": ["vanuatu", "vatican city", "venezuela", "vietnam"],
    "y": ["yemen"],
    "z": ["zambia", "zimbabwe"],
}
JA_COUNTRIES = {
    "ア": [
        "アルバニア",
        "アルジェリア",
        "アメリカ",
        "アンゴラ",
        "アイスランド",
        "アイルランド",
        "アラブシュチョウコクレンポウ",
        "アルメニア",
    ],
    "イ": [
        "イギリス",
        "インド",
        "インドネシア",
        "イラク",
        "イスラエル",
        "イタリア",
    ],
    "ウ": ["ウクライナ", "ウルグアイ"],
    "エ": [
        "エクアドル",
        "エジプト",
        "エルサルバドル",
        "エストニア",
        "エチオピア",
        "エイコク",
        "エリトリア",
    ],
    "オ": ["オーストラリア", "オーストリア"],
    "カ": ["カンボジア", "カタール", "カンコク"],
    "ガ": ["ガンビア", "ガーナ", "ガイヤナ"],
    "キ": ["キューバ", "キプロス", "キタマケドニア"],
    "ギ": ["ギニア"],
    "ク": ["クロアチア", "クウェート"],
    "グ": ["グリーンランド", "グアテマラ"],
    "ケ": ["ケニア"],
    "コ": [
        "コロンビア",
        "コンゴ",
        "コスタリカ",
        "コソボ",
        "コンゴミンシュウキョウワコク",
        "コートジボワール",
    ],
    "ゴ": ["ゴウシュウ"],
    "サ": ["サウジアラビア"],
    "ザ": ["ザンビア"],
    "シ": ["シンガポール", "シリア"],
    "ジ": ["ジャマイカ", "ジンバブエ", "ジョージア", "ジブチ"],
    "ス": [
        "スコットランド",
        "スロバキア",
        "スロベニア",
        "スリランカ",
        "スイス",
    ],
    "セ": ["セキドウギニア", "セネガル", "セイシェル", "セルビア"],
    "ソ": ["ソロモンショトウ", "ソマリア"],
    "タ": ["タヒチ", "タンザニア", "タイ"],
    "チ": [
        "チュウオウアフリカ",
        "チャド",
        "チリ",
        "チュウゴク",
        "チェコ",
        "チュニジア",
    ],
    "デ": ["デンマーク"],
    "ト": ["トリニダード・トバゴ", "トルコ"],
    "ド": ["ドミニカキョウワコク"],
    "ナ": ["ナミビア", "ナイジェリア"],
    "ニ": ["ニューギニア", "ニュージーランド", "ニカラグア"],
    "ネ": ["ネパール"],
    "ハ": ["ハイチ"],
    "バ": ["バハマ", "バルバドス"],
    "パ": ["パレスチナ", "パナマ", "パプアニューギニア", "パラグアイ"],
    "ヒ": ["ヒガシティモール"],
    "フ": ["フィンランド", "フランス"],
    "ブ": ["ブラジル", "ブルネイ", "ブルガリア"],
    "プ": ["プエルトリコ"],
    "ベ": ["ベイコク", "ベネズエラ", "ベラルーシ"],
    "ホ": ["ホンジェラス"],
    "ボ": ["ボリビア", "ボスニヤ・ヘルツェゴビナ", "ボツワナ"],
    "ポ": ["ポーランド", "ポルトガル"],
    "マ": ["マカオ", "マダガスカル", "マレーシア", "マルタ"],
    "ミ": ["ミナミアフリカ"],
    "メ": ["メキシコ"],
    "モ": [
        "モルディブ",
        "モーリシャス",
        "モルドバ",
        "モナコ",
        "モウコ",
        "モンゴル",
        "モロッコ",
        "モザンビーク",
        "モンテネグロ",
        "モーリタニア",
    ],
    "ラ": ["ラオス", "ラトビア"],
    "リ": ["リベリア", "リビア", "リトアニア"],
    "ル": ["ルクセンブルク", "ルーマニア"],
    "ロ": ["ロシア"],
}
COUNTRY_EXCEPTIONS = [
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
    "turkey",
    "uruguay",
    "paraguay",
    "hungary",
    "italy",
    "germany",
    "vatican city",
]
MAX_DEPTH = 10


def setup_database_win_losses(conn):
    """create tables if they don't exist"""
    try:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS game_results (
                        id INTEGER PRIMARY KEY,
                        wins INTEGER NOT NULL,
                        losses INTEGER NOT NULL
                    );""")
        # Check if the table is empty, and if so, insert initial values
        cursor.execute("SELECT COUNT(*) FROM game_results")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO game_results (wins, losses) VALUES (0, 0)")
            conn.commit()
    except sqlite3.Error as error:
        print(error)


countries_game_ru_db = create_connection("databases/countries_game_ru.db")
setup_database_win_losses(countries_game_ru_db)
countries_game_eng_db = create_connection("databases/countries_game_eng.db")
setup_database_win_losses(countries_game_eng_db)
countries_game_ja_db = create_connection("databases/countries_game_ja.db")
setup_database_win_losses(countries_game_ja_db)
botoboinya_db = create_connection("databases/botoboinya.db")
setup_database_win_losses(botoboinya_db)
letters = {}
games_active = {}
botoboinya_restart = False
first_country = None
timeout = 120
turn_count = 0


def get_letter(country):
    if country[-1] in "ьыъ":
        letter = country[-2]
    else:
        letter = country[-1]
    return letter


def check_country(country, letter, countries):
    if letter is None:
        if country in COUNTRY_EXCEPTIONS:
            # print('country is exception')
            return False
        print(country, country[0], countries)
        if country[0] in countries and country in countries[country[0]]:
            return True
    else:
        if letter not in countries:
            # print('letter not in dictionary')
            return False
        if country[0] != letter:
            # print('wrong letter')
            return False
        if country in countries[letter]:
            return True
    # print('other reason')
    return False


def calculate_score(country, countries, depth, alpha=float("-inf"), beta=float("inf")):
    countries[country[0]].remove(country)
    player = depth % 2
    letter = get_letter(country)
    if letter in countries:
        possible_countries = tuple(countries[letter])
    else:
        possible_countries = []

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
            value = max(value, calculate_score(i, countries, depth + 1, alpha, beta))
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # beta cut-off
    else:
        value = float("inf")
        for i in possible_countries:
            value = min(value, calculate_score(i, countries, depth + 1, alpha, beta))
            beta = min(beta, value)
            if beta <= alpha:
                break  # alpha cut-off

    countries[country[0]].append(country)
    return value


def calculate_next_country(country, countries):
    countries[country[0]].remove(country)
    possible_countries = tuple(countries[get_letter(country)])
    if not possible_countries:
        return None
    choices = []
    for c in possible_countries:
        score = calculate_score(c, countries, 0)
        choices.append((score, c))
    choices.sort()
    max_eval = choices[-1][0]
    for i in choices.copy():
        if i[0] != max_eval:
            choices.remove(i)
    # print(choices)
    random_country = choice(choices)[1]
    # print(f'Evaluation: {max_eval}')
    countries[choices[-1][1][0]].remove(random_country)
    return random_country


async def send_game_results_ru(inter, win):
    update_game_results(countries_game_ru_db, win)
    wins, loses = get_wins_and_loses(countries_game_ru_db)
    await inter.followup.send(f"Кузобот: {wins}, Человечество: {loses}")


async def send_game_results_eng(inter, win):
    update_game_results(countries_game_eng_db, win)
    wins, loses = get_wins_and_loses(countries_game_eng_db)
    await inter.followup.send(f"Kuzobot: {wins}, Humanity: {loses}")


async def send_game_results_ja(inter, win):
    update_game_results(countries_game_ja_db, win)
    wins, loses = get_wins_and_loses(countries_game_ja_db)
    await inter.followup.send(f"クズボット: {wins}, 人間: {loses}")


async def send_game_results_botoboinya(interaction, win):
    update_game_results(botoboinya_db, win)
    wins, loses = get_wins_and_loses(botoboinya_db)
    output = (
        f"Кузобот: {wins}, Фениксобот: {loses}\nДебют: {str(first_country).capitalize()}"
    )
    if first_country in COUNTRY_EXCEPTIONS:
        output += " (исключение)"
    output += f", Кол-во ходов: {turn_count - 1}"
    await interaction.followup.send(output)


def get_wins_and_loses(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT wins FROM game_results")
    wins = cursor.fetchone()[0]
    cursor.execute("SELECT losses FROM game_results")
    losses = cursor.fetchone()[0]
    return wins, losses


def update_game_results(conn, win):
    """update the win/loss record"""
    try:
        c = conn.cursor()
        if win:
            c.execute("UPDATE game_results SET wins = wins + 1")
        else:
            c.execute("UPDATE game_results SET losses = losses + 1")
        conn.commit()
    except sqlite3.Error as error:
        print(error)


async def country_game_russian_main_function(
    inter, country, countries, used_countries, channel_id
):
    # global games_active, letters
    letter = letters[channel_id]
    if not country:
        return
    if country == "стоп":
        games_active[channel_id] = False
        await inter.followup.send("Игра окончена")
        await send_game_results_ru(inter, True)
        return
    if country == "кот-д ивуар" or country == "кот-д'ивуар":
        country = "кот-д’ивуар"
    if not check_country(country, letter, countries):
        if country in used_countries:
            await inter.followup.send("Такая страна уже была названа.")
            return
        if letter is None and country in COUNTRY_EXCEPTIONS:
            await inter.followup.send(
                f"Нельзя использовать {country.capitalize()} в качестве первой страны."
            )
            return
        if letter is not None and country[0] != letter:
            await inter.followup.send("Вы назвали страну на неправильную букву")
            return
        await inter.followup.send(
            "Вы ошиблись в названии страны. Бот использует этот источник:\n"
            "<https://ru.wikipedia.org/wiki/Список_государств>  "
            'Напишите "стоп", чтобы прекратить игру.'
        )
        return
    used_countries.add(country)
    output_country = calculate_next_country(country, countries)
    used_countries.add(output_country)

    if output_country is None:
        await inter.followup.send(f'Поздравляю, вы прошли "страны"! :tada:')  # Noqa
        games_active[channel_id] = False
        await send_game_results_ru(inter, False)
        return
    letters[channel_id] = get_letter(output_country)
    letter = letters[channel_id]
    await inter.followup.send(f"Мой ход: {output_country.capitalize()}")
    if letter is not None and len(countries[letter]) == 0:
        await inter.followup.send(
            f"Страны на букву {letter.capitalize()} закончились, вы проиграли."
        )
        games_active[channel_id] = False
        await send_game_results_ru(inter, True)
        return
    return


async def country_game_english_main_function(
    inter, country, countries, used_countries, channel_id
):
    # global games_active, letters
    letter = letters[channel_id]
    if not country:
        return
    if country == "stop":
        games_active[channel_id] = False
        await inter.followup.send("The game is over.")
        await send_game_results_eng(inter, True)
        return
    if not check_country(country, letter, countries):
        if country in used_countries:
            await inter.followup.send("Such country has already been named.")
        elif letter is None and country in COUNTRY_EXCEPTIONS:
            await inter.followup.send(
                f"You can't use {country.capitalize()} as your first country."
            )
        elif letter is not None and country[0] != letter:
            await inter.followup.send("Wrong letter.")
        else:
            await inter.followup.send(
                "You made a mistake in the name of the country\n"
                "The bot uses this list of countries:\n"
                "<https://en.wikipedia.org/wiki/List_of_sovereign_states>\n"
                "Type 'stop' to end the game."
            )
        return

    used_countries.add(country)
    output_country = calculate_next_country(country, countries)
    used_countries.add(output_country)

    if output_country is None:
        await inter.followup.send("Congratulations, you won the countries game! :tada:")  # Noqa
        await send_game_results_eng(inter, False)
        games_active[channel_id] = False
        return
    letters[channel_id] = get_letter(output_country)
    letter = letters[channel_id]
    await inter.followup.send(f"My turn: {output_country.capitalize()}")
    if letter is not None and len(countries[letter]) == 0:
        await inter.followup.send(
            f"You ran out of countries that end in {letter.capitalize()}. You lost."
        )
        games_active[channel_id] = False
        await send_game_results_eng(inter, True)
        return
    return


def to_katakana(text):
    converted = []
    for char in text:
        code = ord(char)
        # Check if the character is a Hiragana character in the typical conversion range.
        if 0x3041 <= code <= 0x3096:
            converted.append(chr(code + 0x60))
        else:
            converted.append(char)
    return "".join(converted)


replacements = {
    "アラブ首長国連邦": "アラブシュチョウコクレンポウ",
    "コンゴ民主共和国": "コンゴミンシュウキョウワコク",
    "ソロモン諸島": "ソロモンショトウ",
    "ドミニカ共和国": "ドミニカキョウワコク",
    "中国": "チュウゴク",
    "中央アフリカ": "チュウオウアフリカ",
    "北朝鮮": "キタチョウセン",
    "南アフリカ": "ミナミアフリカ",
    "台湾": "タイワン",
    "日本": "ニホン",
    "米国": "ベイコク",
    "英国": "イギリス",
    "蒙古": "モウコ",
    "赤道ギニア": "セキドウギニア",
    "韓国": "カンコク",
    "香港": "ホンコン",
    "北マケドニア": "キタマケドニア",
    "東ティモール": "ヒガしティモール",
}
output_replacements = {to_katakana(value): key for key, value in replacements.items()}
ALL_JA_COUNTRIES = [
    "アフガニスタン",
    "アルバニア",
    "アルジェリア",
    "アメリカ",
    "ベイコク",
    "アンゴラ",
    "アルゼンチン",
    "オーストラリア",
    "ゴウシュウ",
    "オーストリア",
    "バハマ",
    "バーレーン",
    "バングラデシュ",
    "バルバドス",
    "ベルギー",
    "ベリーズ",
    "ブータン",
    "ボリビア",
    "ボスニヤ・ヘルツェゴビナ",
    "ボツワナ",
    "ブラジル",
    "ブルネイ",
    "ブルガリア",
    "カンボジア",
    "カメルーン",
    "カナダ",
    "チュウオウアフリカ",
    "チャド",
    "チリ",
    "チュウゴク",
    "コロンビア",
    "コンゴ",
    "コスタリカ",
    "クロアチア",
    "キューバ",
    "キプロス",
    "チェコ",
    "デンマーク",
    "ドミニカキョウワコク",
    "エクアドル",
    "エジプト",
    "エルサルバドル",
    "セキドウギニア",
    "エストニア",
    "エチオピア",
    "フィジー",
    "フィンランド",
    "フランス",
    "ガンビア",
    "ドイツ",
    "ガーナ",
    "エイコク",
    "イギリス",
    "ギリシャ",
    "グリーンランド",
    "グレナダ",
    "グアテマラ",
    "ギニア",
    "ガイヤナ",
    "ハイチ",
    "オランダ",
    "ホンジェラス",
    "ホンコン",
    "ハンガリー",
    "アイスランド",
    "インド",
    "インドネシア",
    "イラン",
    "イラク",
    "アイルランド",
    "イスラエル",
    "イタリア",
    "ジャマイカ",
    "ニホン / ニッポン",
    "ヨルダン",
    "ケニア",
    "コソボ",
    "クウェート",
    "ラオス",
    "ラトビア",
    "レバノン",
    "リベリア",
    "リビア",
    "リトアニア",
    "ルクセンブルク",
    "マカオ",
    "マダガスカル",
    "マラウィ",
    "マレーシア",
    "マルタ",
    "モルディブ",
    "モーリシャス",
    "メキシコ",
    "モルドバ",
    "モナコ",
    "モウコ",
    "モンゴル",
    "モロッコ",
    "モザンビーク",
    "ミャンマー",
    "ナミビア",
    "ネパール",
    "ニューギニア",
    "ニュージーランド",
    "ニカラグア",
    "ナイジェリア",
    "キタチョウセン",
    "ノルウェー",
    "オーマン",
    "パキスタン",
    "パレスチナ",
    "パナマ",
    "パプアニューギニア",
    "パラグアイ",
    "ペルー",
    "フィリピン",
    "ポーランド",
    "ポルトガル",
    "カタール",
    "ルーマニア",
    "ロシア",
    "ルワンダ",
    "サウジアラビア",
    "スコットランド",
    "セネガル",
    "セイシェル",
    "シンガポール",
    "スロバキア",
    "スロベニア",
    "ソロモンショトウ",
    "ソマリア",
    "ミナミアフリカ",
    "カンコク",
    "スペイン",
    "スリランカ",
    "スーダン",
    "スウェーデン",
    "スイス",
    "シリア",
    "タヒチ",
    "タイワン",
    "タンザニア",
    "タイ",
    "トリニダード・トバゴ",
    "チュニジア",
    "トルコ",
    "ウガンダ",
    "ウクライナ",
    "アラブシュチョウコクレンポウ",
    "ウルグアイ",
    "バチカン",
    "ベネズエラ",
    "ベトナム",
    "ウェールズ",
    "イエメン",
    "コンゴミンシュウキョウワコク",
    "ザンビア",
    "ジンバブエ",
    "モンテネグロ",
    "セルビア",
    "ジョージア",
    "ベラルーシ",
    "カザフスタン",
    "ウズベキスタン",
    "トルクメニスタン",
    "タジキスタン",
    "リヒテンシュタイン",
    "サンマリノ",
    "エリトリア",
    "ヒガシティモール",
    "ジブチ",
    "アゼルバイジャン",
    "アルメニア",
    "プエルトリコ",
    "コートジボワール",
    "キルギスタン",
    "モーリタニア",
    "キタマケドニア",
]


async def country_game_ja_main_function(
    inter, country, countries, used_countries, channel_id
):
    if country in replacements:
        country = replacements[country]
    country = to_katakana(country)
    letter = letters[channel_id]
    if not country:
        return
    if country == "stop":
        games_active[channel_id] = False
        await inter.followup.send("ゲームは終了しました。")
        await send_game_results_ja(inter, True)
        return
    if not check_country(country, letter, countries):
        if country in used_countries:
            await inter.followup.send("その国はすでに挙がっています。")
        elif letter is None and country in COUNTRY_EXCEPTIONS:
            await inter.followup.send(
                f"最初の国として {country.capitalize()} は使えません。"
            )
        elif letter is not None and country[0] != letter:
            await inter.followup.send("間違った文字です。")
        elif country in ALL_JA_COUNTRIES:
            await inter.followup.send(
                f"国名は {country[-1]} で終わることはできません。なぜなら、この文字で始まる国がないからです。"
            )
        else:
            await inter.followup.send(
                "国名に間違いがあります。\n"
                "ボットは以下の国名リストを使用しています： <https://www.learn-japanese-adventure.com/japanese-country-names.html>\n"
                "ゲームを終了するには「stop」と入力してください。"
            )
        return

    used_countries.add(country)
    output_country = calculate_next_country(country, countries)
    used_countries.add(output_country)

    if output_country is None:
        await inter.followup.send("おめでとうございます！国名ゲームに勝利しました！")  # Noqa
        await send_game_results_ja(inter, False)
        games_active[channel_id] = False
        return
    letters[channel_id] = get_letter(output_country)
    letter = letters[channel_id]
    if output_country in output_replacements:
        output_country = output_replacements[output_country]
    await inter.followup.send(f"私の番です：{output_country.capitalize()}")
    if letter is not None and len(countries[letter]) == 0:
        await inter.followup.send(
            f"最後が {letter.capitalize()} で終わる国がなくなりました.\n"
            f"あなたの負けです。"
        )
        games_active[channel_id] = False
        await send_game_results_ja(inter, True)
        return
    return


class Countries(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="countries-ru", description="Начать игру в 'Страны'")
    async def country_game_russian(self, inter: disnake.ApplicationCommandInteraction):
        channel_id = inter.channel.id
        if games_active.get(channel_id):
            await inter.send("Игра уже началась в этом канале.")
            return

        countries_dict = {i: COUNTRIES[i][:] for i in COUNTRIES}

        games_active[channel_id] = True
        letters[channel_id] = None
        used_countries = set()

        await inter.send('Игра "Страны" началась! Отправьте название страны.')

        while games_active[channel_id]:
            try:
                message = await self.bot.wait_for("message", timeout=timeout)
                if message.author == self.bot.user or message.channel.id != channel_id:
                    continue
                await country_game_russian_main_function(
                    inter,
                    message.content.strip().lower(),
                    countries_dict,
                    used_countries,
                    channel_id,
                )
            except asyncio.TimeoutError:
                games_active[channel_id] = False
                await send_game_results_ru(inter, True)
                await inter.followup.send(
                    "Время вышло! Игра окончена, так как игроки не ответили."
                )

    @commands.slash_command(name="countries-eng", description="Play the game 'Countries'")
    async def country_game_english(self, inter: disnake.ApplicationCommandInteraction):
        channel_id = inter.channel.id
        if games_active.get(channel_id):
            await inter.send("The game has already been started in this channel.")
            return

        countries_dict = {i: ENG_COUNTRIES[i][:] for i in ENG_COUNTRIES}
        used_countries = set()

        games_active[channel_id] = True
        letters[channel_id] = None

        await inter.send("The game has started! Name a country first.")

        while games_active[channel_id]:
            try:
                message = await self.bot.wait_for("message", timeout=timeout)
                if message.author == self.bot.user or message.channel.id != channel_id:
                    continue
                await country_game_english_main_function(
                    inter,
                    message.content.strip().lower(),
                    countries_dict,
                    used_countries,
                    channel_id,
                )
            except asyncio.TimeoutError:
                games_active[channel_id] = False
                await send_game_results_eng(inter, True)
                await inter.followup.send(
                    "Time out! The game is over because nobody answered."
                )

    @commands.slash_command(
        name="countries-ja",
        description="日本語で国のしりとり",
        guild_ids=GUILD_IDS,
    )
    async def country_game_japanese(self, inter: disnake.ApplicationCommandInteraction):
        channel_id = inter.channel.id
        if games_active.get(channel_id):
            await inter.send("このチャンネルではすでにゲームが始まっています。")
            return

        countries_dict = {i: JA_COUNTRIES[i][:] for i in JA_COUNTRIES}
        used_countries = set()

        games_active[channel_id] = True
        letters[channel_id] = None

        await inter.send("ゲームが始まりました！まず国名を挙げてください。")

        while games_active[channel_id]:
            try:
                message = await self.bot.wait_for("message", timeout=timeout)
                if message.author == self.bot.user or message.channel.id != channel_id:
                    continue
                await country_game_ja_main_function(
                    inter,
                    message.content.strip().lower(),
                    countries_dict,
                    used_countries,
                    channel_id,
                )
            except asyncio.TimeoutError:
                games_active[channel_id] = False
                await send_game_results_ja(inter, True)
                await inter.followup.send(
                    "タイムアウト！誰も答えなかったので、ゲームは終了しました。"
                )


def setup(bot):
    bot.add_cog(Countries(bot))
