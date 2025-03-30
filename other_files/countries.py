from random import choice

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
MAX_DEPTH = 11


def get_letter(country):
    if country[-1] in "ьыъ":
        letter = country[-2]
    else:
        letter = country[-1]
    return letter


def check_country(country, letter, countries):
    # print(country, letter)
    if letter is None:
        if country in COUNTRY_EXCEPTIONS:
            # print('country is exception')
            return False
        if country[0] in countries and country in countries[country[0]]:
            return True
    if letter is not None:
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
    print(choices)
    random_country = choice(choices)[1]
    print(f"Evaluation: {max_eval}")
    countries[choices[-1][1][0]].remove(random_country)
    return random_country
