#!/usr/bin/env python3
"""Render the curated reasoned-parallels report and CSV lists from the source data.

Source of truth: ``src/motifs/reasoned_parallels.py`` (the hand-authored groups).
This script pulls live motif titles from the built indexes and writes, into this
folder:

- ``reasoned_parallels.csv``        — flat list (one row per member).
- ``reasoned_parallels_triads.csv`` — groups spanning all three indexes.
- ``reasoned-parallels.md``         — the full write-up (framing + every group).

Run (from the repo root, after ``mytho motifs``)::

    PYTHONPATH=src python3 docs/motifs/crosswalk/build_reasoned_lists.py
"""
from __future__ import annotations

import csv
from pathlib import Path

from motifs import reasoned_parallels as rp
from motifs import store

OUT = Path(__file__).parent
IDX_LABEL = {"berezkin": "Berezkin", "tmi": "TMI", "atu": "ATU"}

FRAMING = """\
# Параллельные мотивы между индексами — по рассуждению

*Ручное содержательное сопоставление трёх индексов (Берёзкин, TMI, ATU): какие
мотивы/типы параллельны **по смыслу**, а не по совпадению слов. Дополняет
лексический слой (`find_parallels.py` / «Possible parallels»), который ловит
совпадение слов в названиях и пропускает понятийные параллели с разной
формулировкой. Источник данных — `src/motifs/reasoned_parallels.py`; на страницах
мотивов эти группы показаны разделом «Parallels by reasoning».*

## Почему три индекса параллельны неравномерно

Берёзкин и TMI — оба **индексы мотивов** (этиологические/космологические единицы),
поэтому глубоко параллельны в «первобытной» зоне (главы Берёзкина A/B/H/I ↔ глава
TMI A «Мифологические» и F). ATU — **индекс типов** (целых сюжетов), поэтому
пересекается с ними только там, где мотив «тянет» на целый сюжет (герой-змееборец,
волшебное бегство, похищенная жена-птица). Для «происхождения Плеяд» типа ATU просто
не существует. Отсюда: **Берёзкин↔TMI — самая богатая пара, ATU подключается редко и
только на «сюжетообразующих» мотивах.** И именно в Берёзкин↔TMI лексический метод
провалился сильнее всего — там одно и то же понятие названо несовпадающими словами.

## Оговорки

Это тематические/структурные суждения, не доказанные тождества. Многие связи —
**один-ко-многим** (один мотив Берёзкина ↔ целое поддерево TMI), направление и объём
единиц у каталогов разные, а часть «триад» на стороне ATU держится слабее (тип-новелла
против точечного мотива). Уверенность помечена (`high`/`medium`); неполнота допустима —
это подсказки для сравнителя, а не финальные вердикты.

"""


def title_of(index, mid):
    d = store.load_index(index)
    key = "types" if index == "atu" else "motifs"
    for r in d[key]:
        if r["id"] == mid:
            return r.get("name", "")
    return "?? (not found)"


def main():
    # enrich members with titles once
    groups = []
    for g in rp.GROUPS:
        members = [(idx, mid, title_of(idx, mid)) for idx, mid in g["members"]]
        indexes = {idx for idx, _, _ in members}
        groups.append({**g, "members": members, "indexes": indexes})

    # flat CSV
    with open(OUT / "reasoned_parallels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["theme", "title", "confidence", "index", "id", "motif_title", "spans"])
        for g in groups:
            spans = "+".join(sorted(IDX_LABEL[i] for i in g["indexes"]))
            for idx, mid, ttl in g["members"]:
                w.writerow([g["theme"], g["title"], g["confidence"], idx, mid, ttl, spans])

    # triads CSV
    with open(OUT / "reasoned_parallels_triads.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["theme", "title", "confidence", "berezkin", "tmi", "atu"])
        for g in groups:
            if len(g["indexes"]) == 3:
                per = {"berezkin": [], "tmi": [], "atu": []}
                for idx, mid, _ in g["members"]:
                    per[idx].append(mid)
                w.writerow([g["theme"], g["title"], g["confidence"],
                            " ".join(per["berezkin"]), " ".join(per["tmi"]), " ".join(per["atu"])])

    # markdown report
    triads = [g for g in groups if len(g["indexes"]) == 3]
    pairs = [g for g in groups if len(g["indexes"]) == 2]
    with open(OUT / "reasoned-parallels.md", "w") as f:
        W = f.write
        W(FRAMING)
        W(f"## Сводка\n\nВсего групп: **{len(groups)}** "
          f"(трёхсторонних: **{len(triads)}**, попарных: **{len(pairs)}**).\n\n")
        W("| Тема | Уверенность | Охватывает | Участников |\n|---|---|---|---|\n")
        for g in groups:
            spans = " + ".join(sorted(IDX_LABEL[i] for i in g["indexes"]))
            W(f"| {g['title']} | {g['confidence']} | {spans} | {len(g['members'])} |\n")

        def dump(title, gs):
            W(f"\n## {title}\n")
            for g in gs:
                spans = " + ".join(sorted(IDX_LABEL[i] for i in g["indexes"]))
                W(f"\n### {g['title']}  ·  _{g['confidence']}_  ·  {spans}\n\n")
                W(f"{g['note']}\n\n")
                W("| Индекс | Код | Название |\n|---|---|---|\n")
                for idx, mid, ttl in g["members"]:
                    W(f"| {IDX_LABEL[idx]} | `{mid}` | {ttl} |\n")

        dump("Трёхсторонние параллели (Берёзкин ↔ TMI ↔ ATU)", triads)
        dump("Попарные параллели", pairs)

        W("\n## Что лексический метод упустил vs поймал\n\n"
          "- **Упустил** (иная лексика): ныряльщик за землёй, космическая охота, "
          "звёздный муж, похищение огня/света, Полифем, восхождение по стреле, "
          "космическое яйцо, дуализм творцов. Это фундаментальные мифологические "
          "параллели с несовпадающими названиями.\n"
          "- **Поймал** (почти дословные метки): бегство с препятствиями "
          "(`L72`↔`D672`), «Соловей и медянка», происхождение смерти от ложной вести "
          "(`H36A`↔`A1335.1`).\n")
    print(f"wrote reasoned_parallels.csv, reasoned_parallels_triads.csv, reasoned-parallels.md "
          f"({len(groups)} groups, {len(triads)} triads)")


if __name__ == "__main__":
    main()
