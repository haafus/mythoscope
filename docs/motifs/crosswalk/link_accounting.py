#!/usr/bin/env python3
"""Generate the cross-index link-accounting report from the built data.

Counts, per index-pair, how many links each approach established, how many were
*new* on top of the previous approaches (cumulative union of undirected edges),
and the running total — plus the heuristic/reasoned suggestion layers. Writes
``link-accounting.md`` in this folder.

Run (from the repo root, after ``mytho motifs``)::

    PYTHONPATH=src python3 docs/motifs/crosswalk/link_accounting.py
"""
from __future__ import annotations

import itertools
from pathlib import Path

from motifs import reasoned_parallels as rp
from motifs import store

OUT = Path(__file__).parent
# Edges recovered by the data-defect cleaning this cannot recompute from the
# already-cleaned data; recorded from the cleaning-commit audits (see git log).
DEFECT_RECOVERED = {"berezkin_atu": 16, "berezkin_tmi": 6}


def undirected(fwd_map):
    return {frozenset((a, b)) for a, bs in (fwd_map or {}).items() for b in bs}


def main():
    cw = store.load_crosswalk()
    par = store.load_parallels()
    atu = store.load_index("atu")
    atu_ids = {t["id"] for t in atu["types"]}
    aliases = atu.get("aliases", {})

    # confirmed relations as undirected edge sets
    constit = undirected(cw["atu_to_tmi"])
    defin = undirected(cw["atu_to_tmi_defining"])
    note = undirected(cw["atu_to_tmi_note"])
    summ = undirected(cw["atu_to_tmi_summary"])
    bz_atu = undirected(cw["berezkin_to_atu"])
    bz_tmi = undirected(cw["berezkin_to_tmi"])

    inf = {"at": set(), "bt": set(), "ba": set()}
    seen = set()
    for side, byid in cw.get("inferred", {}).items():
        for mid, lst in byid.items():
            for e in lst:
                key = frozenset(((side, mid), (e["index"], e["id"])))
                if key in seen:
                    continue
                seen.add(key)
                pair = frozenset((side, e["index"]))
                bucket = ("at" if pair == frozenset(("atu", "tmi"))
                          else "bt" if pair == frozenset(("berezkin", "tmi")) else "ba")
                inf[bucket].add(frozenset((mid, e["id"])))

    # alias-rescue: Berezkin->ATU refs that resolved through an old number
    rescued = 0
    for m in store.load_index("berezkin")["motifs"]:
        for ref in m.get("atu_refs") or []:
            if ref not in atu_ids and (aliases.get(ref) or aliases.get(ref.rstrip("*"))):
                rescued += 1

    # suggestion layers
    def par_edges(pred):
        s = set()
        for side, byid in par.get("adjacency", {}).items():
            for mid, lst in byid.items():
                for e in lst:
                    if pred(e):
                        s.add(frozenset(((side, mid), (e["index"], e["id"]))))
        return s
    lex_a = par_edges(lambda e: e.get("tier") == "A")
    lex_b = par_edges(lambda e: e.get("tier") == "B")
    reasoned = set()
    for g in rp.GROUPS:
        for (ia, ma), (ib, mb) in itertools.combinations(g["members"], 2):
            if ia != ib:
                reasoned.add(frozenset(((ia, ma), (ib, mb))))

    def block(title, steps):
        lines = [f"\n### {title}\n",
                 "| # | Подход | Рёбер | Новых | Итог |", "|---|---|---|---|---|"]
        acc = set()
        for i, (name, s) in enumerate(steps, 1):
            new = s - acc
            acc |= s
            lines.append(f"| {i} | {name} | {len(s)} | +{len(new)} | {len(acc)} |")
        return "\n".join(lines), len(acc)

    at_block, at_total = block("ATU ↔ TMI", [
        ("явно в датасете (`atu_seq`, constituent)", constit),
        ("распарсили из меток (defining)", defin),
        ("распарсили из заметок TMI (`Type N`, AaTh-резолв)", note),
        ("распарсили из summary ATU (inline-коды)", summ),
        ("замыкание троек (inferred)", inf["at"])])
    ba_block, ba_total = block("Berezkin ↔ ATU", [
        ("распарсили из титулов (`atu_refs`, +alias-rescue, +чистка)", bz_atu),
        ("замыкание троек (через TMI-мотив)", inf["ba"])])
    bt_block, bt_total = block("Berezkin ↔ TMI", [
        ("распарсили из mapsofmyths (`tmi_refs` — кураторские Thompson-id из "
         "free-text поля узла; единственный *прямой* мост, +чистка)", bz_tmi),
        ("замыкание троек (через defining-мотив)", inf["bt"])])

    grand = at_total + ba_total + bt_total
    with open(OUT / "link-accounting.md", "w") as f:
        f.write(f"""# Учёт межиндексных связей — по подходам

*Сколько связей установил каждый подход, сколько из них новых (сверх предыдущих)
и сколько стало всего. «Ребро» — неориентированная связь между узлами двух
индексов в рамках одного отношения; «новых» = прирост к объединению предыдущих
шагов. Сгенерировано `link_accounting.py` из `crosswalk.json` / `parallels.json`
/ `reasoned_parallels.py`.*

## Подтверждённые связи (накопительно)
{at_block}
{ba_block}
{bt_block}

> **«Явно в датасете»** в строгом смысле — только `atu_seq` (чистая CSV-колонка
> Trilogy). Всё остальное **парсится из текста**: defining/note/summary — из
> меток и прозы ATU/TMI; `atu_refs` — из титулов Берёзкина; `tmi_refs` — из
> free-text поля узла mapsofmyths (курируется Берёзкиным/Дувакиным на стороне
> источника, но приходит текстом, который мы разбираем и чистим). «Прямой» у
> `tmi_refs` — это «единственный прямой мост Берёзкин↔TMI», а не готовый словарь.

## Отдельные вклады (входят в числа выше)

- **Старыми версиями типов ATU (alias-rescue):** **{rescued}** рёбер Berezkin↔ATU —
  цитаты на до-2004 номера, спасённые через `former_ids`/`aliases`.
- **Исправление дефектов данных:** чистка «грязных» ссылок (скобки, звёзды, `†`,
  `+`-склейки, гомоглифы) вернула висевшие в никуда рёбра —
  **+{DEFECT_RECOVERED['berezkin_atu']}** Berezkin↔ATU (`atu_refs`) и
  **+{DEFECT_RECOVERED['berezkin_tmi']}** Berezkin↔TMI (`tmi_refs`),
  итого **+{sum(DEFECT_RECOVERED.values())}**; попутно убрано ~186 битых ссылок.
- **Зеркальные ссылки:** **0** новых неориентированных рёбер — зеркало делает
  каждое ребро видимым с обоих концов (навигация), а не создаёт связи.
- **Замыкания (все три):** **{len(inf['at']) + len(inf['ba']) + len(inf['bt'])}**
  рёбер ({len(inf['at'])} + {len(inf['ba'])} + {len(inf['bt'])}).
- **Ещё применяли:** конкорданс **AaTh→ATU** (Wikidata) — резолвит номера AaTh в
  заметках TMI (внутри шага 3); нормализация имён/мойбейка — рёбер не даёт.

## Слои-подсказки (кандидаты, не подтверждённые связи)

| Подход | Пар |
|---|---|
| эвристика лексическая, tier A | {len(lex_a)} |
| эвристика лексическая, tier B | {len(lex_b)} |
| рассуждениями (reasoned parallels) | {len(reasoned)} |

## Итоги по трём парам: было → стало

| Пара | Было (базовый подход) | Стало (все подходы) | Прирост |
|---|---|---|---|
| ATU ↔ TMI | {len(constit)} | **{at_total}** | +{at_total - len(constit)} |
| Berezkin ↔ ATU | {len(bz_atu)} | **{ba_total}** | +{ba_total - len(bz_atu)} |
| Berezkin ↔ TMI | {len(bz_tmi)} | **{bt_total}** | +{bt_total - len(bz_tmi)} |
| **Всего подтверждённых** | {len(constit) + len(bz_atu) + len(bz_tmi)} | **{grand}** | +{grand - len(constit) - len(bz_atu) - len(bz_tmi)} |

Плюс **{len(lex_a) + len(lex_b) + len(reasoned)}** подсказок сверху (отдельными слоями).
""")
    print(f"wrote link-accounting.md: ATU-TMI {at_total}, BZ-ATU {ba_total}, "
          f"BZ-TMI {bt_total}, grand {grand}")


if __name__ == "__main__":
    main()
