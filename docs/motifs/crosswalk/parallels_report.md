# Параллельные мотивы без записанных связей

Лексическое сопоставление (TF-IDF по названию+описанию; отдельный сигнал по названию как фильтр точности). Вычтены все существующие рёбра cross-walk. Tier A — высокая уверенность (≥2 общих значимых слова в названии или очень сильное совпадение описаний); Tier B — эхо по одному слову, нужен просмотр.

| Пара | Кандидатов всего | Tier A |
|---|---|---|
| ATU ~ TMI | 602 | 382 |
| BZ ~ TMI | 2871 | 1446 |
| BZ ~ ATU | 29 | 21 |
| **Треугольники BZ~TMI~ATU** | 39 | — |


## ATU ~ TMI — Tier A (топ 30 из 382)

| ATU | название | TMI | название | title | doc | общих |
|---|---|---|---|---|---|---|
| `277` | The King of the Frogs | `B245.1` | King Of Frogs | 1.00 | 0.63 | 2 |
| `750B` | Hospitality Rewarded | `Q45` | Hospitality Rewarded | 1.00 | 0.39 | 2 |
| `1824` | Parody Sermon | `K1961.1.2.1` | Parody Sermon | 1.00 | 0.69 | 2 |
| `159B` | Enmity of Lion and Man | `A2494.7.3` | Enmity Between Lion And Man | 1.00 | 0.53 | 2 |
| `335` | Death's Messengers | `Z111.6` | Death's Messengers | 1.00 | 0.59 | 2 |
| `709A` | The Sister of Nine Brothers | `P253.0.4` | One Sister And Ten Brothers | 1.00 | 0.46 | 2 |
| `709A` | The Sister of Nine Brothers | `P253.0.2` | One Sister And Two Brothers | 1.00 | 0.46 | 2 |
| `709A` | The Sister of Nine Brothers | `P253.0.3` | One Sister And Three (Four) Brothers | 1.00 | 0.46 | 2 |
| `836` | Pride is Punished | `Q331` | Pride Punished | 1.00 | 0.63 | 2 |
| `952*` | A Sausage and a Revolver | `K437.3` | Sausage As Revolver | 1.00 | 0.74 | 2 |
| `986` | The Lazy Husband | `W111.4` | Lazy Husband | 1.00 | 0.40 | 2 |
| `1448*` | Burned and Underbaked Bread | `S54.1` | Burned And Underbaked Bread | 1.00 | 0.74 | 3 |
| `1575*` | The Clever Shepherd | `J1115.9` | Clever Shepherd | 1.00 | 0.53 | 2 |
| `1641D` | The Sham Physician | `K1955` | Sham Physician | 1.00 | 0.43 | 2 |
| `1833E` | God Is Dead | `A108.1` | God Of The Dead | 1.00 | 0.60 | 2 |
| `2260` | The Golden Key | `F886.1` | Golden Key | 1.00 | 0.56 | 2 |
| `545A` | The Cat Castle | `F771.4.2` | Cat Castle | 1.00 | 0.36 | 2 |
| `546` | The Clever Parrot | `J1118.1` | Clever Parrot | 1.00 | 0.69 | 2 |
| `594*` | The Magic Bridle | `D1209.1` | Magic Bridle | 1.00 | 0.58 | 2 |
| `756E*` | Charity Rewarded | `V410` | Charity Rewarded | 1.00 | 0.51 | 2 |
| `910N` | The Magic Box | `D1174` | Magic Box | 1.00 | 0.49 | 2 |
| `1319G*` | Boot Mistaken for an Axe-sheath | `J1772.11` | Boot Mistaken For An Axe-Sheath | 1.00 | 0.96 | 4 |
| `1420` | The Lover's Gift Regained | `K1357` | Lover's Gift Regained | 1.00 | 0.69 | 3 |
| `1693` | The Literal Fool | `J2450` | Literal Fool | 1.00 | 0.65 | 2 |
| `1889H` | Submarine Otherworld | `F133` | Submarine Otherworld | 1.00 | 0.45 | 2 |
| `1890B*` | Fatal Bread | `J1824` | Fatal Bread | 1.00 | 0.60 | 2 |
| `200B` | Why Dogs Sniff at One Another | `A2471.1.1` | Why Dogs Sniff At One Another | 1.00 | 0.54 | 2 |
| `760` | The Unquiet Grave | `E410` | The Unquiet Grave | 1.00 | 0.36 | 2 |
| `1577` | Blind Men Duped into Fighting | `K1081` | Blind Men Duped Into Fighting | 1.00 | 0.70 | 4 |
| `875A` | Girl's Riddling Answer Betrays a Theft | `H582.1` | Riddling Answer Betrays Theft | 0.98 | 0.52 | 4 |

## BZ ~ TMI — Tier A (топ 30 из 1446)

| BZ | название | TMI | название | title | doc | общих |
|---|---|---|---|---|---|---|
| `A18` | The Sun boat | `A723` | Boat Of The Sun | 1.00 | 0.83 | 2 |
| `B80` | Measuring of the world | `A1186` | Measuring The World | 1.00 | 0.89 | 2 |
| `C31b` | The wise owl | `B122.0.3` | Wise Owl | 1.00 | 0.82 | 2 |
| `I35C` | God the craftsman | `A141` | God As Craftsman | 1.00 | 0.72 | 2 |
| `I75` | World ages | `A1101` | The Four Ages Of The World | 1.00 | 0.70 | 2 |
| `I87B` | The quest for a strong adversary | `H1225` | Quest For A Strong Adversary | 1.00 | 0.85 | 3 |
| `I141` | The magic wand | `D1254.1` | Magic Wand | 1.00 | 0.83 | 2 |
| `J57` | Son of the Sun | `A225` | Son Of The Sun | 1.00 | 0.70 | 2 |
| `L15a1` | Achilles' heel | `Z311` | Achilles Heel | 1.00 | 0.79 | 2 |
| `L100D` | The entrapped suitors | `K1218.1` | The Entrapped Suitors | 1.00 | 0.51 | 2 |
| `L126` | The bird indifferent to pain | `Z49.3` | The Bird Indifferent To Pain | 1.00 | 0.46 | 3 |
| `M106d` | My name is "Son-in-law" | `P265` | Son-In-Law | 1.00 | 0.75 | 2 |
| `M106h` | Holding down the hat | `K1252` | Holding Down The Hat | 1.00 | 0.63 | 2 |
| `M116` | Wisdom of hidden old man saves kingdom | `J151.1` | Wisdom Of Hidden Old Man Saves Kingdom | 1.00 | 0.69 | 5 |
| `M157D` | Pulling up a turnip | `Z49.9` | Pulling Up The Turnip | 1.00 | 0.73 | 2 |
| `M196` | The silence wager | `J2511` | The Silence Wager | 1.00 | 0.64 | 2 |
| `A5` | The Sun and the Moon are males | `R9.1.3` | Sun And Moon Imprison Each Other | 1.00 | 0.58 | 2 |
| `A6` | The Sun and the Moon are females | `R9.1.3` | Sun And Moon Imprison Each Other | 1.00 | 0.54 | 2 |
| `B28E` | The Moon organizes the world | `A695` | Moon As Next World | 1.00 | 0.66 | 2 |
| `B56` | Fire tongue of the crocodile | `A2344.1.1.2` | Why Crocodile Has No Tongue | 1.00 | 0.81 | 2 |
| `B79` | Cosmic egg | `A641` | Cosmic Egg | 1.00 | 0.66 | 2 |
| `B89` | Owl as a king of birds | `B242.1.8` | Owl As King Of Birds | 1.00 | 0.88 | 3 |
| `C30A` | A pound of flesh | `J1161.2` | Pound Of Flesh | 1.00 | 0.59 | 2 |
| `F3A` | The pregnant man | `T578` | Pregnant Man | 1.00 | 0.84 | 1 |
| `F18A` | The long penis | `F547.3.1` | Long Penis | 1.00 | 0.74 | 2 |
| `F30` | Snake paramour | `B613.1` | Snake Paramour | 1.00 | 0.55 | 2 |
| `F45A` | Conception from wind | `T524` | Conception From Wind | 1.00 | 0.77 | 2 |
| `F98` | God and a cow | `A132.9.1` | Cow As God | 1.00 | 0.83 | 2 |
| `H1A` | The originator of death the first sufferer | `K1681` | Originator Of Death First Sufferer | 1.00 | 0.69 | 3 |
| `I62` | Milky Way is a river | `A778.3` | Milky Way As A River | 1.00 | 0.87 | 3 |

## BZ ~ ATU — Tier A (топ 30 из 21)

| BZ | название | ATU | название | title | doc | общих |
|---|---|---|---|---|---|---|
| `B125A` | Nightingale and blindworm | `234` | The Nightingale and the Blindworm | 1.00 | 0.65 | 2 |
| `K27T` | Climbing contest | `1073` | Climbing Contest | 1.00 | 0.58 | 2 |
| `K119d` | Puss in boots | `545B` | Puss in Boots | 1.00 | 0.35 | 2 |
| `K167` | The children's king | `892` | The Children of the King | 1.00 | 0.36 | 2 |
| `M101A` | Animals learn to fear men | `157` | Animals Learn to Fear Men | 1.00 | 0.51 | 3 |
| `M199e` | Carrying the horse | `1201` | Carrying the Horse | 1.00 | 0.38 | 2 |
| `K40` | One will be eaten today and another tomorrow | `1541***` | 'Today for Money, Tomorrow for None' | 0.81 | 0.38 | 2 |
| `B104B` | Woman is changed in a woodpecker | `751A` | The Farmwife is Changed into a Woodpecker | 0.81 | 0.35 | 2 |
| `K56a4c` | To wash something black making it white | `1312*` | Trying to Wash Black Animal White | 0.80 | 0.47 | 3 |
| `L108G` | To wash a black one | `1312*` | Trying to Wash Black Animal White | 0.79 | 0.44 | 2 |
| `K11B` | Reeds from bird’s bones | `984` | Palace from Bird Bones | 0.74 | 0.35 | 2 |
| `A8` | The Sun, the Moon and the Star are three siblings | `328A*` | Three Brothers Steal Back the Sun, Moon, and Star | 0.72 | 0.47 | 3 |
| `D1A` | Mother-in-law is the Fire | `903C*` | Mother-in-law and Daughter-in-law | 0.70 | 0.48 | 2 |
| `I87c1` | A mouse makes a boat | `135*` | The Mouse Makes a Boat of a Bread-crust | 0.69 | 0.53 | 3 |
| `M74E` | To divide the cheese biting from both parts | `51***` | The Fox as Umpire to Divide Cheese | 0.67 | 0.44 | 2 |
| `M29z1` | The Bald-headed | `1871D` | The Cynic and the Bald-headed Man | 0.66 | 0.42 | 2 |
| `B105` | She daughter-in-law is transformed | `903C*` | Mother-in-law and Daughter-in-law | 0.64 | 0.40 | 2 |
| `K27q1` | Lion’s milk in the lion’s skin | `214B` | The Donkey in Lion's Skin | 0.56 | 0.36 | 2 |
| `I39` | Rainbow road or bridge | `1005` | A Bridge (Road) of Carcasses | 0.56 | 0.35 | 2 |
| `M38a2` | The hen cooks her eggs | `219E**` | The Hen that Laid the Golden Eggs | 0.55 | 0.36 | 2 |
| `M187` | Snail is a participant of the race | `275C*` | The Race of Frog and Snail | 0.53 | 0.37 | 2 |

## Треугольники — все три ребра параллельны, часть связей отсутствует (39)

| BZ | TMI | ATU | отсутствуют связи |
|---|---|---|---|
| `M29z1` The Bald-headed | `J1442.9` The Cynic And The Bald-Headed Man | `1871D` The Cynic and the Bald-headed Man | BZ-TMI, BZ-ATU |
| `A32D` Man in the Moon | `A751.10.1` Joshua As Man In The Moon | `751E*` Man in the Moon | BZ-TMI, BZ-ATU, ATU-TMI |
| `I87c1` A mouse makes a boat | `B295.1` Mouse Makes Boat Of Bread-Crust | `135*` The Mouse Makes a Boat of a Bread-crust | BZ-TMI, BZ-ATU |
| `B105` She daughter-in-law is transformed | `P262.1` Bad Relations Between Mother-In-Law And Daughter-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `D1A` Mother-in-law is the Fire | `P262.1` Bad Relations Between Mother-In-Law And Daughter-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `A2` Several suns | `F961.1.3` Several Suns In Sky | `1334**` Two Suns | BZ-TMI, BZ-ATU, ATU-TMI |
| `A32D` Man in the Moon | `X1851` Man In Moon Lets Himself Down | `751E*` Man in the Moon | BZ-TMI, BZ-ATU, ATU-TMI |
| `I37D` Mushrooms are excrements | `A2794.1` Why Mushrooms Are Slimy | `297B` The War of the Mushrooms | BZ-TMI, BZ-ATU, ATU-TMI |
| `A32D` Man in the Moon | `A751.4` Man In The Moon: Tarring Of The Moon | `751E*` Man in the Moon | BZ-TMI, BZ-ATU |
| `A32D` Man in the Moon | `A751.10.2` Jacob As Man In The Moon | `751E*` Man in the Moon | BZ-TMI, BZ-ATU, ATU-TMI |
| `D1A` Mother-in-law is the Fire | `P262` Mother-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `K119d` Puss in boots | `B582.1.1` Animal Wins Wife For His Master (Puss In Boots) | `545B` Puss in Boots | BZ-TMI, BZ-ATU |
| `A32D` Man in the Moon | `A751.10` Particular Individual Is Man In The Moon | `751E*` Man in the Moon | BZ-TMI, BZ-ATU, ATU-TMI |
| `A32D` Man in the Moon | `A751.5` Man In The Moon From Scratches Or Paint | `751E*` Man in the Moon | BZ-TMI, BZ-ATU, ATU-TMI |
| `M199e` Carrying the horse | `K72` Deceptive Contest In Carrying A Horse | `1201` Carrying the Horse | BZ-TMI, BZ-ATU, ATU-TMI |
| `B105` She daughter-in-law is transformed | `S51.1` Cruel Mother-In-Law Plans Death Of Daughter-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `L108G` To wash a black one | `J1909.6` Numskull Tries To Wash Black Hen White | `1312*` Trying to Wash Black Animal White | BZ-TMI, BZ-ATU |
| `K56a4c` To wash something black making it white | `J1909.6` Numskull Tries To Wash Black Hen White | `1312*` Trying to Wash Black Animal White | BZ-TMI, BZ-ATU |
| `B105` She daughter-in-law is transformed | `S54` Cruel Daughter-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `A32D` Man in the Moon | `Q235.1` Man Put In Moon For Cursing God | `751E*` Man in the Moon | BZ-TMI, BZ-ATU, ATU-TMI |
| `B125A` Nightingale and blindworm | `A2241.5` Nightingale Borrows Blindworm's Eye | `234` The Nightingale and the Blindworm | BZ-TMI, BZ-ATU |
| `D2` Woman gives birth to the fire | `T554` Woman Gives Birth To Animal | `299` The Mountain Gives Birth to a Mouse | BZ-TMI, BZ-ATU, ATU-TMI |
| `D2` Woman gives birth to the fire | `T554.10` Woman Gives Birth To A Bird | `299` The Mountain Gives Birth to a Mouse | BZ-TMI, BZ-ATU, ATU-TMI |
| `D2` Woman gives birth to the fire | `T554.7` Woman Gives Birth To A Snake | `299` The Mountain Gives Birth to a Mouse | BZ-TMI, BZ-ATU, ATU-TMI |
| `A8` The Sun, the Moon and the Star are three siblings | `R9.1.3` Sun And Moon Imprison Each Other | `328A*` Three Brothers Steal Back the Sun, Moon, and Star | BZ-TMI, BZ-ATU, ATU-TMI |
| `D2` Woman gives birth to the fire | `T556` Woman Gives Birth To A Demon | `299` The Mountain Gives Birth to a Mouse | BZ-TMI, BZ-ATU, ATU-TMI |
| `D2` Woman gives birth to the fire | `T554.8.1` Woman Gives Birth To Toad | `299` The Mountain Gives Birth to a Mouse | BZ-TMI, BZ-ATU, ATU-TMI |
| `D2` Woman gives birth to the fire | `A1234.4` Earth Gives Birth To Woman | `299` The Mountain Gives Birth to a Mouse | BZ-TMI, BZ-ATU, ATU-TMI |
| `B105` She daughter-in-law is transformed | `C173` Daughter-In-Law Tabu | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `D2` Woman gives birth to the fire | `T555.1.1` Woman Gives Birth To Pumpkin | `299` The Mountain Gives Birth to a Mouse | BZ-TMI, BZ-ATU, ATU-TMI |
| `B105` She daughter-in-law is transformed | `J1111.3` Clever Daughter-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `D1A` Mother-in-law is the Fire | `C171` Mother-In-Law Tabu | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `B105` She daughter-in-law is transformed | `K2214.2` Treacherous Daughter-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `D1A` Mother-in-law is the Fire | `S51` Cruel Mother-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `B105` She daughter-in-law is transformed | `G79.2` Woman Eats Daughter-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `D1A` Mother-in-law is the Fire | `T417.1` Mother-In-Law Seduces Son-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `D1A` Mother-in-law is the Fire | `T417` Son-In-Law Seduces Mother-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
| `D2` Woman gives birth to the fire | `T554.11` Supernaturally Impregnated Woman Gives Birth To Dragon | `299` The Mountain Gives Birth to a Mouse | BZ-TMI, BZ-ATU, ATU-TMI |
| `D1A` Mother-in-law is the Fire | `N365.4` Man Unwittingly Lies With Mother-In-Law | `903C*` Mother-in-law and Daughter-in-law | BZ-TMI, BZ-ATU, ATU-TMI |
