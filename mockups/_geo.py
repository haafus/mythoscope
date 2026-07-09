"""Approximate coordinates for the map mockups. No lat/long exists in the source
data, so we resolve a tradition label to a point two ways:

  * Berezkin traditions -> the centroid of their areal subregion (areal_path L2);
  * TMI / ATU culture labels -> a small country/people gazetteer.

Coordinates are rough centroids meant only to place a dot in the right part of the
world for a prototype — not authoritative locations. (lon, lat).
"""

# Berezkin areal-scheme L2 subregion -> centroid.
SUBREGION = {
    "AUSTRALIA": (134, -25),
    "ARCTIC": (-165, 68), "NORTHEAST ASIA": (162, 62),
    "CHINA – KOREA": (115, 35), "RYUKYU – KURIL ISLANDS": (140, 33), "TAIWAN": (121, 24),
    "ANTILLES AND GUIANA": (-60, 6), "CENTRAL AND EASTERN AMAZONIA": (-58, -4),
    "EASTERN AND SOUTHEASTERN BRAZIL": (-45, -18), "LLANOS AND SOUTHERN VENEZUELA": (-66, 5),
    "MONTAÑA, BOLIVIA, GUAPORE": (-65, -14), "SOUTHERN AMAZONIA": (-58, -12),
    "WESTERN AND NORTHWESTERN AMAZONIA": (-72, -4),
    "ECUADOR AND CENTRAL ANDES": (-76, -10), "HONDURAS – PANAMA": (-84, 12),
    "NORTHERN ANDES": (-74, 5), "NORTHWEST MEXICO AND MESOAMERICA": (-100, 20),
    "MADAGASCAR": (47, -19),
    "CALIFORNIA": (-120, 38),
    "COAST – PLATEAU (OREGON, WASHINGTON, SOUTHERN BRITISH COLUMBIA)": (-121, 47),
    "GREAT BASIN": (-116, 40), "GREAT SOUTHWEST": (-110, 34), "MIDWEST": (-90, 43),
    "NORTHWEST COAST": (-131, 54), "SUBARCTIC (NORTHERN ATHABASKAN)": (-132, 62),
    "THE NORTHEAST": (-75, 45),
    "BALTOSCANDIA": (20, 61), "MIDDLE VOLGA – PERM": (52, 57), "WESTERN AND EASTERN SLAVS": (30, 52),
    "MELANESIA": (150, -6), "POLYNESIA, MICRONESIA": (-172, -10),
    "NORTHERN AND CENTRAL PLAINS": (-100, 44), "SOUTHERN PLAINS": (-99, 35), "THE SOUTHEAST": (-85, 33),
    "AMUR – SAKHALIN": (140, 51), "EASTERN SIBERIA": (120, 63),
    "SOUTHERN SIBERIA - MONGOLIA": (100, 50), "WESTERN SIBERIA": (75, 60),
    "CHACO": (-61, -24), "SOUTHERN CONE": (-70, -42),
    "ARYAN AND SOUTH INDIA": (78, 20), "IRAN – CENTRAL ASIA": (60, 33), "NEAR EAST": (40, 33),
    "NORTH CAUCASUS – ASIA MINOR": (44, 43), "TURKESTAN": (65, 42),
    "SOUTH CAUCASUS – ASIA MINOR": (44, 40),
    "BANTU": (25, -6), "EASTERN SUDANIC, SAHARAN, ADAMAUA": (22, 12),
    "SOUTHWEST AFRICA": (18, -22), "WEST AFRICA": (-2, 9),
    "BURMA, INDOCHINA": (100, 18), "NUSANTARA": (115, -2), "SOUTH ASIA": (80, 15),
    "TIBET, NORTHEAST INDIA": (90, 28),
    "ANCIENT GREECE AND ROME": (18, 40), "BALKAN-CARPATHIANS": (24, 45),
    "HORN OF AFRICA": (42, 8), "NORTH AFRICA": (5, 30), "SOUTHERN AND WESTERN EUROPE": (5, 47),
}

# Country / people gazetteer for TMI & ATU labels (lowercased keys).
GAZ = {
    "india": (79, 22), "hindu": (79, 22), "buddhist myth": (85, 27), "indic": (79, 22),
    "irish": (-8, 53), "irish myth": (-8, 53), "ireland": (-8, 53),
    "jewish": (35, 31), "hebrew": (35, 31), "biblical": (35, 31),
    "icelandic": (-19, 65), "icel": (-19, 65),
    "italian": (12, 43), "italian novella": (12, 43), "roman": (12, 42),
    "chinese": (105, 35), "china": (105, 35), "japanese": (138, 37), "korean": (128, 37),
    "greek": (22, 39), "greek myth": (22, 39), "ancient greece": (22, 39),
    "spanish": (-4, 40), "spanish exempla": (-4, 40), "spain": (-4, 40), "catalan": (2, 42),
    "portuguese": (-8, 40), "basque": (-2, 43),
    "lithuanian": (24, 55), "latvian": (25, 57), "estonian": (26, 59), "esthonian": (26, 59),
    "finnish": (26, 63), "finnish-swedish": (24, 62), "livonian": (24, 58),
    "u.s": (-98, 39), "u.s.": (-98, 39), "united states": (-98, 39), "american": (-98, 39),
    "north carolina": (-79, 35), "new york": (-75, 43), "missouri french": (-92, 38),
    "spanish-american": (-99, 22), "mexican": (-102, 23), "puerto rican": (-66, 18),
    "english": (-1, 52), "england": (-1, 52), "scottish": (-4, 57), "scotch": (-4, 57),
    "welsh": (-3.5, 52), "wales": (-3.5, 52), "breton": (-3, 48), "cornish": (-5, 50),
    "german": (10, 51), "austrian": (14, 47), "swiss": (8, 47), "frisian": (6, 53),
    "dutch": (5, 52), "flemish": (4, 51), "danish": (10, 56), "norwegian": (9, 61),
    "swedish": (16, 62), "lappish": (24, 68),
    "french": (2, 47), "french canadian": (-72, 47), "french-canadian": (-72, 47),
    "walloon": (5, 50),
    "russian": (40, 56), "ukrainian": (31, 49), "byelorussian": (28, 53), "byelarusians": (28, 53),
    "polish": (19, 52), "czech": (15, 50), "slovak": (19, 48), "slovenian": (15, 46),
    "serbian": (21, 44), "croatian": (16, 45), "bulgarian": (25, 43), "bulgarians": (25, 43),
    "rumanian": (25, 46), "romanians": (25, 46), "hungarian": (19, 47), "gypsy": (22, 46),
    "slavic": (30, 52), "wends": (14, 51), "karelian": (32, 63), "wepsian": (35, 60),
    "cheremis": (48, 56), "cheremis/mari": (48, 56), "mordvin": (45, 54), "votyak": (52, 57),
    "vogul": (63, 62), "ostyak": (68, 62), "samoyed": (75, 68), "zyrian": (54, 63),
    "turkish": (35, 39), "anatolia turks": (33, 39), "greek (modern)": (22, 39),
    "georgian": (44, 42), "georgians": (44, 42), "armenian": (45, 40), "armenians": (45, 40),
    "abkhaz": (41, 43), "kabardian": (43, 43), "ossetian": (44, 43), "chechen": (46, 43),
    "persian": (53, 32), "persians": (53, 32), "iranian": (53, 32), "afghan": (66, 34),
    "kurdish": (44, 37), "arabian": (45, 24), "aramaic": (40, 34), "syrian": (38, 35),
    "iraqi": (44, 33), "palestinian": (35, 32), "lebanese": (36, 34), "jordanian": (36, 31),
    "saudi arabian": (45, 24), "qatar": (51, 25), "yemenite": (48, 15), "oman": (57, 21),
    "egyptian": (30, 27), "moroccan": (-6, 32), "algerian": (3, 28), "tunisian": (9, 34),
    "libyan": (18, 27), "sudanese": (30, 15), "north african": (8, 30),
    "ethiopian": (40, 9), "somalian": (46, 6), "swahili": (39, -6),
    "kazakh": (68, 48), "uzbek": (64, 41), "kirghiz": (75, 41), "turkmen": (59, 39),
    "tadzhik": (71, 39), "kalmyk": (46, 46), "chuvash": (47, 55), "bashkir": (56, 54),
    "tatar": (50, 55), "karachays": (42, 44), "balkar": (43, 43), "nogay": (46, 44),
    "buryat": (108, 52), "mongol": (105, 47), "mongols": (105, 47), "yakut": (129, 64),
    "tuvinian": (94, 52), "altai": (87, 51), "khakas": (91, 53), "siberian": (95, 60),
    "chukchi": (172, 66), "koryak": (166, 61), "kamchadal": (159, 56), "gilyak": (142, 53),
    "nanai": (137, 49), "evenki": (110, 58), "even": (140, 62), "nenets": (72, 68),
    "khanty": (68, 62), "mansi": (63, 62), "selkup": (82, 65), "ket": (88, 63),
    "ainu": (143, 43), "eskimo": (-100, 68), "eskimo (greenland)": (-42, 72),
    "eskimo (labrador)": (-60, 55), "inuit": (-90, 68), "asiatic eskimo": (-173, 65),
    "n. am. indian": (-100, 45), "s. am. indian": (-60, -10), "central american indian": (-90, 15),
    "aztec": (-99, 19), "maya": (-89, 17), "mayan": (-89, 17), "inca": (-72, -13),
    "navajo": (-109, 36), "hopi": (-110, 36), "cherokee": (-84, 35), "iroquois": (-76, 43),
    "ojibwa": (-90, 47), "blackfoot": (-113, 49), "tlingit": (-135, 58), "haida": (-132, 53),
    "pomo": (-123, 39), "shuswap": (-121, 51), "thompson": (-121, 50), "menominee": (-88, 45),
    "hawaii": (-156, 20), "hawaiian": (-156, 20), "maori": (174, -41), "samoa": (-172, -14),
    "tahiti": (-149, -17), "tuamotu": (-142, -17), "marquesas": (-140, -9), "tonga": (-175, -21),
    "cook group": (-160, -20), "society is": (-149, -17), "micronesia": (150, 7),
    "melanesia": (150, -6), "melanesian": (150, -6), "new guinea": (144, -6),
    "fiji": (178, -18), "indonesia": (118, -2), "indonesian": (118, -2), "philippine": (122, 13),
    "philippine (tinguian)": (120, 17), "malay": (102, 3), "javanese": (110, -7),
    "borneo": (114, 1), "sumatra": (101, 0),
    "africa": (20, 3), "africa (ekoi)": (9, 6), "africa (fang)": (11, 1), "africa (luba)": (24, -8),
    "africa (basuto)": (28, -29), "africa (zulu)": (31, -29), "bantu": (25, -6),
    "west indies": (-70, 18), "jamaica": (-77, 18), "brazilian": (-52, -12),
    "argentina": (-64, -35), "chilean": (-71, -35), "peruvian": (-76, -10),
    "venezuelan": (-66, 7), "costa rican": (-84, 10), "nicaraguan": (-85, 13), "congolese": (23, -1),
    "australian": (134, -25), "tibetan": (90, 31), "burmese": (96, 21), "cambodian": (105, 12),
    "thai": (101, 15), "vietnamese": (106, 16), "sri lankan": (81, 8), "nepalese": (84, 28),
    "pakistani": (69, 30), "babylonian": (44, 32), "assyrian": (43, 36), "sumerian": (46, 31),
}

_SUFFIX = (" myth", " novella", " exempla", " folklore", " tale", " tales")


def _canon(s):
    return " ".join((s or "").lower().replace("_", " ").split())


def gaz_coord(label):
    k = _canon(label)
    if k in GAZ:
        return GAZ[k]
    base = k.split("(")[0].strip().rstrip(":")
    if base in GAZ:
        return GAZ[base]
    for suf in _SUFFIX:
        if base.endswith(suf) and base[: -len(suf)] in GAZ:
            return GAZ[base[: -len(suf)]]
    return None


# Real per-tradition coordinates for the Berezkin catalogue, committed as a snapshot
# (mockups/tradition-coords.json, areal_id -> [lat, lon]) so the map mockups place
# each tradition at its actual location without a full motif-pipeline run. Regenerate
# the snapshot with src/motifs/sources/mapsofmyths.py (refresh).
_BEREZKIN_COORDS = None


def berezkin_coords():
    """``{areal_id: [lat, lon]}`` from the committed snapshot (cached, read once)."""
    global _BEREZKIN_COORDS
    if _BEREZKIN_COORDS is None:
        import json
        from pathlib import Path
        path = Path(__file__).with_name("tradition-coords.json")
        try:
            _BEREZKIN_COORDS = json.loads(path.read_text(encoding="utf-8")).get("coordinates", {})
        except FileNotFoundError:
            _BEREZKIN_COORDS = {}
    return _BEREZKIN_COORDS
