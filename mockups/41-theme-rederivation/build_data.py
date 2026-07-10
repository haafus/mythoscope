"""Data-driven re-derivation of the Berezkin theme taxonomy (mockup 41).

Instead of taking Berezkin's 13 hand-assigned theme groups as given, cluster the motif
catalogue *by meaning* (BGE-M3 embeddings) and ask what themes the content itself proposes —
then compare the two. Pipeline:

  1. embeddings (Berezkin block of the cached BGE-M3 matrix), L2-normalised;
  2. **UMAP** to 2-D (the scatter you look at) and to 10-D (a denoised space for clustering —
     UMAP-10 beats PCA-64 and raw on both cluster purity and agreement with the hand themes);
  3. **level-1** KMeans (16 natural clusters) → each hand-named;
  4. **level-2** KMeans inside every level-1 cluster → sub-categories (labelled by their most
     widespread motif);
  5. **comparison** to the 13 hand themes: contingency, purity, adjusted Rand, and a per-theme
     verdict — which hand themes the data recovers cleanly and which it dissolves.

Headline: the celestial / cosmogonic / formulaic themes are recovered as clean, tight clusters
(Formulae 100 % pure; Sun-Moon, Stars, Cosmogony, the death-messenger, the trickster *casting*
all isolate), while the two catch-alls **Adventures** and **Tricks** have no natural cluster of
their own — the data reorganises them into narrative complexes (magic-wife, ogre-escape,
animal-fable, ogre-dupe, revenge…) that cut straight across the Adventures/Tricks line.

Build needs `umap-learn` (pip install umap-learn).  Run:
    python mockups/41-theme-rederivation/build_data.py
"""
import json
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
K1 = 16

GN = {1: "Солнце/Луна", 2: "Звёзды", 3: "Космогония", 4: "Смерть", 5: "Люди", 6: "Культура",
      7: "Флора/фауна", 8: "Чудовища", 9: "Отождествления", 10: "Приключения", 11: "Трюки",
      12: "Имена", 13: "Формулы", 0: "(нет)"}
GEN = {1: "Sun/Moon", 2: "Stars", 3: "Cosmogony", 4: "Death", 5: "Humans", 6: "Culture",
       7: "Flora/fauna", 8: "Monsters", 9: "Identif.", 10: "Adventures", 11: "Tricks",
       12: "Names", 13: "Formulae", 0: "(none)"}

# Curated level-1 names, keyed by a *signature motif id* (the cluster's most-widespread motif)
# so the label follows content, not the (permutation-dependent) KMeans index.
PROSE = {
    "A32":   ("Лунный лик, Солнце и Луна", "Небесные светила: пятна на луне, человек на луне, солнце-и-луна как супруги или братья, затмение-нападение. Чистый небесный блок."),
    "I72":   ("Звёзды, созвездия и радужный змей", "Звёзды-люди, Плеяды, Большая Медведица, космическая охота, Млечный Путь, радужный змей/мост — звёздная и атмосферная этиология."),
    "B3A":   ("Космогония: первичные воды, земля, небо", "Первичные воды и ныряльщик за землёй, растущая земля, небо близко к земле, всемирный потоп — ядро творения мира."),
    "B2A":   ("Происхождение людей и тело", "Земля-женщина, восхождение человечества, амазонки, vagina dentata, телесные аномалии, опасная женщина — антропогония и тело."),
    "J26":   ("Чудесное рождение и брачный партнёр-животное", "Младенцы из воды, подменённый ребёнок, невозможное рождение, супруг-змей/животное — рождение и брак с иным."),
    "K25":   ("Магическая жена и трудные задачи", "Дева-лебедь и её поиск, трудные задачи тестя/царя, ложная жена, утраченная и возвращённая женщина — комплекс волшебной жены."),
    "K2":    ("Бегство от людоеда и героические приключения", "Разрушенная лестница, спасение в огне, побег от людоеда, змееборец, чудесные спутники — героический авантюрный слой."),
    "J1":    ("Мстители, похищения и демоны", "Мстящие герои, отец-соперник, похищенная/утонувшая жена, ребёнок обещан демону, демонов огонь — месть и похищение."),
    "L93A":  ("Животная басня: помощники и благодарные звери", "Помогающая лиса, благодарные животные, черепаха-победитель, бой за птенцов, золотоносное животное — животная басня и помощники."),
    "L42":   ("Одурачивание людоеда и незадачливый подражатель", "Герой в доме людоеда, неблагодарный спасённый, враг-подражатель трикстера, запретная комната, пари-уговор — обман силача и провал копииста."),
    "L72":   ("Магическое бегство и добывание благ", "Погоня с бросанием предметов, таинственная хозяйка, глупое подражание, подслушанные тайны, добытые ценности — магическое бегство и похищение культурных благ."),
    "L19B":  ("Чудовища, проглатыватель и уязвимое тело", "Многоглавые существа, Иона-проглатыватель, внешняя душа, обожжённая кожа, уязвимое место — чудовища и уязвимое/аномальное тело."),
    "M29B":  ("Кастинг трикстера (кто плут)", "Отождествление трикстера с конкретным зверем: лиса/шакал/койот, заяц, ворон, обезьяна. Не сюжет, а региональный кастинг главного плута."),
    "M29b1": ("Кастинг жертвы (кто дурак)", "Зеркало трикстерского кастинга: «волк/медведь/лев/тигр/гиена/ягуар — неудачник». Кто из крупных зверей играет одурачиваемого."),
    "N14":   ("Сказочные формулы (зачины/концовки)", "Формульная риторика märchen: «сказитель на свадьбе», «текло по усам», «если не умерли — живут поныне», начальные формулы. 100% чистый стилистический пласт."),
    "H36ff": ("Происхождение смерти: неверный вестник", "«Смерть и ворон/хамелеон/койот/ящерица» — африкано-евразийский комплекс перепутанной вести о бессмертии. Тематически монолитен."),
}


def main():
    import umap
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    M = bz["motifs"]
    E = np.load(ROOT / "outputs" / "motifs" / "raw" / "bge_m3.npy")
    X = E[-len(M):].astype(np.float32)
    X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    grp = np.array([int(r.get("motif_group_num") or 0) for r in M])
    br = np.array([len(r.get("traditions") or []) for r in M])

    u2 = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, metric="cosine",
                   random_state=42).fit_transform(X)
    u10 = umap.UMAP(n_components=10, n_neighbors=15, min_dist=0.0, metric="cosine",
                    random_state=42).fit_transform(X)
    lab = KMeans(n_clusters=K1, n_init=8, random_state=0).fit(u10).labels_

    purity = sum(Counter(grp[lab == c]).most_common(1)[0][1] for c in range(K1)) / len(M)
    ari = adjusted_rand_score(grp, lab)

    # order level-1 clusters by size; name via signature motif; build sub-clusters
    sizes = sorted(range(K1), key=lambda c: -(lab == c).sum())
    cl_of = {}                                   # kmeans index -> ordinal display id
    clusters = []
    for disp, c in enumerate(sizes):
        idx = np.where(lab == c)[0]
        sig = max(idx, key=lambda i: br[i])
        sid = M[sig]["id"]
        name, desc = PROSE.get(sid, (M[sig].get("name", sid), ""))
        dom = [{"g": int(g), "ru": GN[g], "en": GEN[g], "n": int(n)}
               for g, n in Counter(grp[idx]).most_common(4)]
        tops = sorted(idx, key=lambda i: -br[i])[:8]
        top = [{"c": M[i]["id"], "name": M[i].get("name", ""), "b": int(br[i])} for i in tops]
        k2 = int(np.clip(round(len(idx) / 55), 2, 5))
        subs = []
        if len(idx) >= 8:
            sl = KMeans(n_clusters=k2, n_init=5, random_state=0).fit(u10[idx]).labels_
            for s in range(k2):
                si = idx[sl == s]
                if not len(si):
                    continue
                rep = max(si, key=lambda i: br[i])
                subs.append({"label": M[rep].get("name", ""), "n": int(len(si)),
                             "ex": [M[i].get("name", "") for i in sorted(si, key=lambda i: -br[i])[:3]]})
            subs.sort(key=lambda s: -s["n"])
        clusters.append({"id": disp, "sig": sid, "name": name, "desc": desc, "n": int(len(idx)),
                         "dom": dom, "top": top, "subs": subs,
                         "purity": round(Counter(grp[idx]).most_common(1)[0][1] / len(idx), 2)})
        cl_of[c] = disp

    # per-hand-theme verdict: how concentrated is each Berezkin theme in the data clusters?
    themes = []
    for g in sorted(GN):
        if g == 0:
            continue
        gi = np.where(grp == g)[0]
        if not len(gi):
            continue
        spread = Counter(cl_of[c] for c in lab[gi])
        top_disp, top_n = spread.most_common(1)[0]
        conc = top_n / len(gi)
        n80 = 0
        acc = 0
        for _, n in spread.most_common():
            acc += n; n80 += 1
            if acc >= 0.8 * len(gi):
                break
        verdict = "recovered" if conc >= 0.45 else "dissolved" if conc < 0.30 else "split"
        themes.append({"g": int(g), "ru": GN[g], "en": GEN[g], "n": int(len(gi)),
                       "conc": round(conc, 2), "top_cluster": int(top_disp),
                       "n_clusters_80": int(n80), "spans": int(len(spread)), "verdict": verdict})
    themes.sort(key=lambda t: -t["conc"])

    # contingency matrix rows=cluster(display) cols=theme(1..13)
    cols = [g for g in range(1, 14)]
    cont = [[int(((lab == inv_disp(cl_of, disp)) & (grp == g)).sum()) for g in cols]
            for disp in range(K1)]

    xs, ys = u2[:, 0].astype(float), u2[:, 1].astype(float)
    xmin, xr = xs.min(), (xs.max() - xs.min()) or 1.0
    ymin, yr = ys.min(), (ys.max() - ys.min()) or 1.0
    pts = [{"x": round((xs[i] - xmin) / xr, 4),
            "y": round((ys[i] - ymin) / yr, 4),
            "t": int(grp[i]), "k": int(cl_of[lab[i]]), "c": M[i]["id"],
            "nm": M[i].get("name", ""), "b": int(br[i])} for i in range(len(M))]

    data = {"n": len(M), "K1": K1, "purity": round(purity, 3), "ari": round(ari, 3),
            "quality": QUALITY, "gnames_ru": GN, "gnames_en": GEN,
            "clusters": clusters, "themes": themes, "cont": cont, "cont_cols": cols,
            "pts": pts}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False,
                                                 separators=(",", ":")) + ";", encoding="utf-8")
    print(f"UMAP-10 · K={K1} · purity {purity:.3f} · ARI-vs-13themes {ari:.3f} · data.js "
          f"~{OUT.stat().st_size // 1024}KB")
    for cl in clusters:
        d = cl["dom"][0]
        print(f"  [{cl['id']:2}] n={cl['n']:4} pur={cl['purity']:.2f} "
              f"dom={d['en']}{d['n']:<4} {cl['name']}")
    print("  theme verdicts:")
    for t in themes:
        print(f"    {t['en']:11} conc={t['conc']:.2f} spans={t['spans']:2} -> {t['verdict']}")


def inv_disp(cl_of, disp):
    for k, v in cl_of.items():
        if v == disp:
            return k
    return -1


# clustering-quality comparison (computed once, reported in the UI). Values from the sweep:
# purity / ARI at K=16 for each reduction. UMAP-10 wins on both.
QUALITY = [
    {"space": "raw 1024-d", "purity": 0.460, "ari": 0.073},
    {"space": "PCA-64", "purity": 0.475, "ari": 0.078},
    {"space": "UMAP-2", "purity": 0.503, "ari": 0.102},
    {"space": "UMAP-10", "purity": 0.513, "ari": 0.120},
]


if __name__ == "__main__":
    main()
