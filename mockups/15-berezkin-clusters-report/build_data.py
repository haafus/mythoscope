"""Berezkin cluster report — data builder.

Runs the per-index biclustering (mockup 06) for the Berezkin index, enriches each
cluster with its macro-area composition (from the tradition areal_path), theme-group
distribution and top motifs, attaches map points (lon/lat per tradition), and merges
in a curated per-cluster analysis (name / boundaries / etiology / connections /
content) written by hand. Emits data.js for the HTML report.

Motif *names* are short catalogue labels; all interpretive prose is original.

Run from repo root:  python mockups/15-berezkin-clusters-report/build_data.py
"""
import importlib.util
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull, Delaunay, QhullError
from sklearn.cluster import DBSCAN

ROOT = Path(__file__).resolve().parents[2]
MOCKS = ROOT / "mockups"
OUT = Path(__file__).resolve().parent / "data.js"


def load_mod(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def canon(s):
    return re.sub(r"\s+", " ", (s or "").strip()).rstrip(".,;:")


# --------------------------------------------------------------------------- #
# Approximate filled "footprint" blobs for a cluster's points.
# DBSCAN groups nearby traditions; singletons (label -1) are dropped as outliers,
# so a stray point never balloons the shape. Each dense group becomes a buffered,
# corner-cut (Chaikin) polygon — an organic contour rather than a raw hull.
# --------------------------------------------------------------------------- #
def _ring(cx, cy, r, n=18):
    return [[round(cx + r * math.cos(2 * math.pi * i / n), 2),
             round(cy + r * math.sin(2 * math.pi * i / n), 2)] for i in range(n)]


def _offset(ring, pad):
    """Push each vertex outward along the mean of its adjacent edge normals so the
    contour encloses the boundary points with a little padding (concave-safe)."""
    n = len(ring)
    area = sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1] for i in range(n))
    if area < 0:                               # force CCW so the right-hand normal is outward
        ring = ring[::-1]
    out = []
    for i in range(n):
        a, p, b = ring[i - 1], ring[i], ring[(i + 1) % n]
        def rnorm(u, v):
            dx, dy = v[0] - u[0], v[1] - u[1]
            L = math.hypot(dx, dy) or 1.0
            return (dy / L, -dx / L)           # right normal (outward for CCW)
        nx, ny = rnorm(a, p)[0] + rnorm(p, b)[0], rnorm(a, p)[1] + rnorm(p, b)[1]
        L = math.hypot(nx, ny) or 1.0
        out.append([round(p[0] + nx / L * pad, 2), round(p[1] + ny / L * pad, 2)])
    return out


def _circumradius(a, b, c):
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-9:
        return float("inf")
    a2, b2, c2 = a[0]**2 + a[1]**2, b[0]**2 + b[1]**2, c[0]**2 + c[1]**2
    ux = (a2 * (b[1] - c[1]) + b2 * (c[1] - a[1]) + c2 * (a[1] - b[1])) / d
    uy = (a2 * (c[0] - b[0]) + b2 * (a[0] - c[0]) + c2 * (b[0] - a[0])) / d
    return math.hypot(ux - a[0], uy - a[1])


def _alpha_rings(P, alpha):
    """Boundary loops of the alpha-complex: Delaunay triangles with circumradius <=
    alpha are 'solid'; edges on exactly one solid triangle are the boundary; stitch
    them into closed rings. Hugs points; ocean-spanning triangles are dropped."""
    tri = Delaunay(P)
    edge_ct = Counter()
    for s in tri.simplices:
        if _circumradius(P[s[0]], P[s[1]], P[s[2]]) <= alpha:
            for e in ((s[0], s[1]), (s[1], s[2]), (s[2], s[0])):
                edge_ct[frozenset(e)] += 1
    bedges = [tuple(e) for e, n in edge_ct.items() if n == 1]
    if not bedges:
        return []
    adj = {}
    for i, j in bedges:
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)
    key = lambda a, b: (a, b) if a < b else (b, a)
    used, rings = set(), []
    for i0, j0 in bedges:
        if key(i0, j0) in used:
            continue
        ring, used_add = [i0], used.add
        used_add(key(i0, j0))
        prev, cur = i0, j0
        while cur != i0:
            ring.append(cur)
            nxt = next((x for x in adj[cur] if x != prev and key(cur, x) not in used), None)
            if nxt is None:
                break
            used_add(key(cur, nxt))
            prev, cur = cur, nxt
        if cur == i0 and len(ring) >= 3:
            rings.append([[round(float(P[k][0]), 2), round(float(P[k][1]), 2)] for k in ring])
    return rings


def _chaikin(poly, iters=2):
    for _ in range(iters):
        out = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            out.append([round(a[0] * 0.75 + b[0] * 0.25, 2), round(a[1] * 0.75 + b[1] * 0.25, 2)])
            out.append([round(a[0] * 0.25 + b[0] * 0.75, 2), round(a[1] * 0.25 + b[1] * 0.75, 2)])
        poly = out
    return poly


def cluster_blobs(points, eps=25.0, alpha=17.0, pad=2.4):
    """points: list of {x:lon, y:lat}. Returns concave (alpha-shape) contours that hug
    the points: a contiguous region becomes one contour, groups genuinely separated by
    ocean get their own tight contour. Isolated strays are dropped first."""
    if not points:
        return []
    P = np.array([[p["x"], p["y"]] for p in points], dtype=float)
    if len(P) >= 4:
        labels = DBSCAN(eps=eps, min_samples=2).fit(P).labels_
        kept = P[labels != -1]
        if len(kept) >= 4:
            P = kept
    if len(P) < 4:
        return [_chaikin(_ring(P[:, 0].mean(), P[:, 1].mean(), pad + 2))]
    try:
        rings = _alpha_rings(P, alpha)
    except (QhullError, ValueError):
        rings = []
    if not rings:                              # fallback: convex hull
        try:
            rings = [[[round(float(x), 2), round(float(y), 2)] for x, y in P[ConvexHull(P).vertices]]]
        except (QhullError, ValueError):
            rings = [_ring(P[:, 0].mean(), P[:, 1].mean(), pad + 2)]
    return [_chaikin(_offset(r, pad)) for r in rings if len(r) >= 3]


# 14 distinct cluster colours (fixed order)
PALETTE = ["#2f6fed", "#12a150", "#d97706", "#9151d8", "#0e9aa7", "#c2410c",
           "#e11d48", "#3a6ea5", "#b5651d", "#7d8b3a", "#a3457e", "#4f7096",
           "#0891b2", "#7c3aed"]

# Curated analysis, keyed by cluster index (biclustering is deterministic:
# random_state=0, arpack; clusters sorted by size). `sig` = a distinctive tradition
# used to assert alignment at build time.
PROSE = {
 0: {"name": "Европейский сказочно-христианский пояс", "sig": "Lithuanians",
     "boundaries": "Балтия, Восточные и Западные славяне, романоязычная Юго-Восточная Европа, финны и эстонцы, Иберия — то есть христианская Европа к северу и западу от балкано-кавказского стыка. Ядро — балто-славянский и финский север, край — Пиренейский полуостров.",
     "etiology": "Общность недавняя и книжно-опосредованная: единый пласт märchen (волшебной сказки типа ATU) и христианской легенды, разнёсшийся с проповедью, лубком и грамотностью. Это не глубокий субстрат, а верхний, исторически молодой слой европейского фольклора.",
     "connections": "Прямо граничит и частично сливается с кластером 1 (Балканы–Кавказ–Передняя Азия): вместе они образуют западноевразийскую сказочную область. Христианская этиология роднит его с романо-славянской периферией кластера 1.",
     "content": "Христианизированная этиология природы (Млечный Путь как дорога Св. Иакова, грибы из слюны Св. Петра, происхождение животных через святых) поверх волшебно-сказочного и трикстерского сюжета. Небесные и календарные объяснения даны через фигуры христианского пантеона."},
 1: {"name": "Балкано-кавказско-переднеазиатский märchen-пояс", "sig": "Anatolia Turks",
     "boundaries": "Балканы, Кавказ, Анатолия, Иран, тюрки Средней Волги и Средней Азии, с заходом в Западную и Северную Европу. Это шов между Европой и Азией — зона максимальной плотности сказочных типов.",
     "etiology": "Тот же механизм диффузии волшебной сказки, но на перекрёстке цивилизаций: здесь сходятся европейский, ближневосточный и центральноазиатский потоки. Многовековой обмен сюжетами через Византию, ислам и тюркский мир.",
     "connections": "Западной стороной сливается с кластером 0 (Европа), восточной — с кластером 2 (литературная Азия). Фактически центральное звено евразийской сказочной цепи.",
     "content": "Классические сказочные ходы: испытания и обманы (молоко львицы в львиной шкуре, засада из ямы, изгнанный трус), а также формулы и загадки. Мифологический слой слабее — доминирует нарратив märchen."},
 2: {"name": "Литературно-эпическая Азия", "sig": "Mongols (Khalkha)",
     "boundaries": "Не единый ареал, а трансконтинентальный пояс: Центральная Азия и Монголия, Тибет, литературная Индия, Шри-Ланка, Китай, Корея, Япония, с античной Грецией на западном конце.",
     "etiology": "Общность объясняется не соседством, а цивилизационной диффузией — распространением сюжетов через письменные традиции (индийская Панчатантра/джатаки, китайские источники) и кочевые эпосы вдоль трансазиатских путей. «Высококультурный» слой поверх географии.",
     "connections": "Западным концом смыкается с кластером 1, южным и восточным — с кластерами 7 (сино-тибетский) и 8 (Океания). Диффузионный «мост», связывающий сказочную Евразию с Индо-Тихоокеанским миром.",
     "content": "Приключенческие и трикстерские сюжеты книжного эпоса: похищения, инцест-табу, животные-цари, испытания героя. Мотивы часто имеют литературных «предков» в санскритских и китайских сводах."},
 3: {"name": "Северноевразийская тайга: сибирские охотники", "sig": "Nanai",
     "boundaries": "Тунгусо-маньчжуры (нанайцы, эвенки, удэгейцы), обские угры (манси, ханты), самодийцы (ненцы, селькупы), якуты, палеоазиаты (чукчи, нивхи) — от Оби до Берингии.",
     "etiology": "Древняя ареальная общность охотников-собирателей и оленеводов таёжно-тундровой зоны: единая шаманская космология и общий пул промысловых этиологий, разошедшихся вдоль сибирского субстрата задолго до письменности.",
     "connections": "Восточным краем (Берингия) смыкается с североамериканскими кластерами 5 и 9 — след древнего берингийского континуума. С юга примыкает к кластеру 2.",
     "content": "Дева-лебедь и два брата, война птиц, хозяйка огня, шаманская образность (бубен — озеро), происхождение промысловых животных. Космология охотника: душа, превращение, посредники между мирами."},
 4: {"name": "Пуэбло, Калифорния и Восточные Вудленды", "sig": "Navajo",
     "boundaries": "Юго-Запад США (навахо, хопи, зуни, пуэбло Тева и Тива), Калифорния (помо, майду, винту), ирокезы Северо-Востока и юго-восток США (чероки, алабама). Земледельческая и полуоседлая Северная Америка.",
     "etiology": "Ареальная общность оседлых и земледельческих культур: мифы эмергенции и происхождения, характерные для обществ с кукурузным комплексом и ритуалом плодородия. Отличается от охотничьих кластеров 5 и 9.",
     "connections": "Часть общего североамериканского массива вместе с 5 и 9, но тематически ближе к «происхождению» (эмергенция), чем к трикстерскому циклу. Космогонические темы роднят с кластером 6.",
     "content": "Потоп (птицы цепляются за небо), выход первопредков из-под земли, люди из палочек, добыча огня насекомым. Акцент на происхождении людей, стихий и социальных норм."},
 5: {"name": "Северо-Западное побережье и Плато: цикл Ворона", "sig": "Tlingit",
     "boundaries": "Тлинкиты, хайда, цимшиан-подобные, береговые салиши, чинук, сахаптины Плато, а также черноногие и оджибве прерий на восточном крае.",
     "etiology": "Ареальная общность рыболовов тихоокеанского Северо-Запада: изобильная среда, потлач и богатая устная традиция дали плотный трикстерско-трансформаторный корпус вокруг фигуры Ворона.",
     "connections": "Северным краем (Берингия) связан с сибирским кластером 3, восточным — с субарктическим 9. Три вместе — грани северного трикстерского пояса Старого и Нового Света.",
     "content": "Цикл Ворона (Ворон и тюлени), трикстеры (скунс, крапивник), кража огня (бобр добывает огонь), превращения человека в оленя, а ножей — в рога. Трансформация как главный механизм."},
 6: {"name": "Транс-тихоокеанский слой Солнца и Луны", "sig": "Toba (incl Pilaga)",
     "boundaries": "Не географический ареал, а разорванная дуга: Мезоамерика и Анды, Гран-Чако и Западная Амазония, Новая Гвинея (Торричелли, арапеш) и Юго-Восточная Австралия. Точки разбросаны по трём континентам вокруг Тихого океана.",
     "etiology": "Ключевой и теоретически самый ценный кластер. Общность не может быть объяснена соседством — это тонкий, но реальный след очень древнего (плейстоценового) общего наследия: небесная этиология Солнца и Луны как один из старейших разделяемых пластов человеческой мифологии (гипотеза Берёзкина о раннем расселении).",
     "connections": "Пересекает все ареальные кластеры, не входя целиком ни в один. Космогоническая тематика связывает его с 4 (эмергенция) и 8 (островная космогония).",
     "content": "Происхождение и характер светил: Солнце, Луна и глаза чудовища; освобождённая Луна; «Солнце ищет свои глаза»; громовой ягуар. Космогония и этиология неба доминируют над бытовым нарративом."},
 7: {"name": "Сино-тибетский и юго-восточноазиатский пояс", "sig": "Mizo (Lushei)",
     "boundaries": "Тибето-бирманцы Северо-Восточной Индии (чины, нага, куки), Юго-Восточная Азия (вьеты, мяо-яо, тайцы), ранний Китай, Бирма, с мадагаскарско-африканским хвостом.",
     "etiology": "Ареальная общность сино-тибетского и австроазиатского мира; африкано-мадагаскарский хвост — след австронезийской миграции на Мадагаскар. Земледельческая горная Юго-Восточная Азия как очаг.",
     "connections": "Северным краем примыкает к кластеру 2 (литературная Азия), южным — к кластеру 8 (Океания). Промежуточное звено азиатско-тихоокеанского градиента.",
     "content": "Космическое яйцо (одно яйцо выброшено), спасение при потопе в плавучем барабане, этиология полос тигра, брачные договоры с животными. Сильны темы происхождения людей и этносов."},
 8: {"name": "Австронезийская Океания", "sig": "Ifugao",
     "boundaries": "Филиппины (Лусон, Минданао), островная Индонезия (тораджа, Тимор), Тайвань (пайвань, рукай), Новая Гвинея (нагорья и побережье), Вануату и Микронезия (Кирибати, Науру).",
     "etiology": "Ареальная общность австронезийского и папуасского Индо-Тихоокеанского мира: расселение мореходов-австронезийцев и древний папуасский субстрат Новой Гвинеи дали единый корпус островной космогонии.",
     "connections": "Западным краем связан с кластером 7 (Юго-Восточная Азия), тематически (космогония) — с кластером 6. Восточная оконечность азиатско-тихоокеанского градиента 2→7→8.",
     "content": "Островная космогония: вылавливание земли из моря, острова, отрезанные рыбой, люди из плодов, две творящие женщины-прародительницы. Происхождение суши, людей и смерти."},
 9: {"name": "Субарктические алгонкины и атабаски", "sig": "Menominee",
     "boundaries": "Алгонкины (кри, оджибве, меномини, наскапи, монтанье) и северные атабаски (чипевайан, кучин) бореальной Канады, с виннебаго на юге.",
     "etiology": "Ареальная общность бореальных охотников: подвижный образ жизни и длинные зимние повествования дали плотный, обособленный трикстерский цикл, отличный от побережного (5) и оседлого (4).",
     "connections": "Часть североамериканского массива с 4 и 5; берингийским краем перекликается с сибирским 3. Обсценный трикстер роднит его с сибирским и, шире, с северноевразийским юмором.",
     "content": "Обсценный трикстерский цикл (трикстер наказывает собственный зад, поедание падающей плоти) и звёздная лора (Большая Медведица — рыболов), росомаха делает море солёным. Юмор и нарушение нормы как структурная ось."},
 10: {"name": "Амазония и Гвиана", "sig": "Warao",
      "boundaries": "Гвиана и Северо-Западная Амазония (варрау, карина, барасана, витото), хиваро (шуар, ачуар), боливийские гуарани. Влажные тропические низменности севера Южной Америки.",
      "etiology": "Ареальная общность амазонских обществ подсечно-огневого земледелия и охоты: плотная сеть обмена мифами по речным системам бассейна Амазонки и Ориноко.",
      "connections": "Соседствует и частично перекрывается с кластером 11 (Центральная Бразилия) — две грани восточно-южноамериканского массива. С запада примыкает к андско-мезоамериканскому ядру кластера 6.",
      "content": "Дерево, раскрывающее ствол; огрицы, пожирающие гениталии; неполное тело, превращающееся в гром; награда за целомудрие. Этиология животных и происхождение людей в тропическом ключе."},
 11: {"name": "Центральная Бразилия: Же и Верхняя Шингу", "sig": "Bororo",
      "boundaries": "Же-язычные центральной Бразилии (кайапо, апинайе, крао, шаванте, суя), Верхняя Шингу (мехинаку, ваура), северо-западные араваки (баниуа), бороро. Саванны и переходные зоны внутренней Бразилии.",
      "etiology": "Тесная ареальная общность обществ с развитыми мужскими домами и обрядами инициации; единый комплекс мифов о происхождении полов и мужского культа (типа Журупари).",
      "connections": "Соседний с кластером 10 (Амазония); вместе они дробят берёзкинский макро-ареал «Восточная Южная Америка» на речной (10) и центрально-бразильский (11).",
      "content": "Гендерно-этиологический комплекс: женщины превращаются в рыб, уходят под землю; мужчины используют части женского тела; происхождение мужского культа. Мифы о первичном социальном порядке и его переустройстве."},
 12: {"name": "Субсахарский трикстерский пояс", "sig": "Hausa",
      "boundaries": "Западноафриканские Гур и Манде (хауса, бамбара, малинке), банту Конго, Восточной и Южной Африки (конго, шона, ганда), йоруба и эдо Западной Африки. Основной массив Тропической Африки.",
      "etiology": "Широкая ареальная общность банту- и нигеро-конголезского мира: расселение банту и плотный обмен между земледельческими обществами дали общий трикстерский и этиологический корпус.",
      "connections": "Соседствует с кластером 13 (африканское происхождение смерти) — вместе они дробят берёзкинскую «Субсахарскую Африку» на трикстерское ядро (12) и комплекс смерти (13).",
      "content": "Трикстер (паук Ананси, заяц), задачи-узнавания, наказание за убийство жены, соревнования в обмане. Этиология и социальная сатира через фигуру плута."},
 13: {"name": "Африканский комплекс происхождения смерти", "sig": "Wolof",
      "boundaries": "Волоф, Кросс-Ривер (эфик, ибибио), Лози, Чокве, восточно-чадские группы — рассеянный, меньший африканский куст на краю трикстерского пояса.",
      "etiology": "Отдельный тематический африканский пласт вокруг классического сюжета «послание смерти» (искажённая весть через хамелеона/зайца) и происхождения смертности — устойчивого маркера африканской мифологии.",
      "connections": "Дочерний по отношению к кластеру 12: та же макро-Африка, но тематически обособлен вокруг смерти, а не трикстера.",
      "content": "Происхождение смерти (весть о бессмертии искажена посланцем), несожжённый/неоживлённый пёс, соревнования в еде, африканский Иов. Этиология конечности жизни и страдания."},
}


def main():
    m06 = load_mod("06-per-index-biclusters/build_data.py", "m06")
    bz = json.load(open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8"))

    name2macro = {}
    for v in bz["traditions"].values():
        ap = v.get("areal_path") or []
        if ap:
            name2macro[canon(v.get("name") or "")] = ap[0][1]
    mid2grp = {r["id"]: (r.get("motif_group") or "").split(" ", 1)[-1] or "—" for r in bz["motifs"]}

    d = m06.bicluster("brz")
    pts_by_k = {}
    for p in d["points"]:
        pts_by_k.setdefault(p["k"], []).append(p)
    clusters = []
    for k, c in enumerate(d["clusters"]):
        macros = Counter(name2macro.get(t, "?") for t in c["traditions"])
        themes = Counter(mid2grp.get(mm["c"], "—") for mm in c["motifs"])
        pr = PROSE.get(k, {})
        # alignment guard
        if pr.get("sig") and not any(pr["sig"] in t for t in c["traditions"][:6]):
            print(f"  ! cluster {k}: expected sig {pr['sig']!r} not in top traditions {c['traditions'][:4]}")
        clusters.append({
            "id": k, "color": PALETTE[k % len(PALETTE)],
            "name": pr.get("name", f"Cluster {k}"),
            "blobs": cluster_blobs(pts_by_k.get(k, [])),
            "n_motif": c["n_motif"], "n_trad": c["n_trad"],
            "macros": [{"name": a, "n": n} for a, n in macros.most_common(6) if a != "?"],
            "themes": [{"name": t, "n": n} for t, n in themes.most_common(4)],
            "traditions": c["traditions"][:24],
            "motifs": [{"c": mm["c"], "n": mm["n"], "s": mm["s"],
                        "grp": mid2grp.get(mm["c"], "—"),
                        "t": mm.get("t", [])[:3]} for mm in c["motifs"][:20]],
            "boundaries": pr.get("boundaries", ""), "etiology": pr.get("etiology", ""),
            "connections": pr.get("connections", ""), "content": pr.get("content", ""),
        })

    data = {"n_motifs": d["n_motifs"], "n_traditions": d["n_traditions"],
            "clusters": clusters, "points": d["points"]}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(clusters)} clusters · {d['n_motifs']} motifs · {d['placed']} placed points · "
          f"data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
