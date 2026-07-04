"""Curated cross-index parallels found by reasoning, not by string similarity.

A hand-authored companion to the lexical ``parallels.py`` layer. Where TF-IDF
matches shared *words* in titles, these groups record shared *concepts* — the
same mytheme catalogued under very different labels across Berezkin, TMI and ATU
(e.g. Berezkin's "Valuables brought from the lower world" = TMI "Earth Diver").
Most of these are invisible to the lexical pass; they are judgement calls, so each
carries a ``confidence`` and the reasoning is spelled out in
``docs/motifs/crosswalk/reasoned-parallels.md``.

Each group lists members as ``(index, id)`` pairs across the indexes; a group with
members in all three indexes is a three-way parallel. Granularity differs by
design: one Berezkin motif often parallels a whole TMI sub-tree, so several
representative ids are listed. Uncertainty is fine and expected — these are
suggestions for a comparativist to weigh, not asserted identities.
"""

from __future__ import annotations

# theme: short slug · title: display label · note: the reasoning · confidence:
# high | medium · members: [(index, id), ...]
GROUPS: list[dict] = [
    # --- Cosmogonic / etiological motifs (Berezkin ↔ TMI; ATU has no tale type) ---
    {"theme": "earth-diver", "title": "Earth-diver cosmogony", "confidence": "high",
     "note": "An animal dives to the sea floor and brings up the mud from which the "
             "earth is made. Berezkin files it as 'Valuables brought from the lower "
             "world' with the diver species as sub-motifs; TMI as 'Earth Diver'. Zero "
             "shared title words, so the lexical pass cannot see it. A812.1 'Devil as "
             "Earth Diver' matches Berezkin's dualistic-diver variants.",
     "members": [("berezkin", "C6"), ("berezkin", "C6A"), ("berezkin", "C6B"),
                 ("berezkin", "C6C"), ("berezkin", "C6c3"), ("tmi", "A812"), ("tmi", "A812.1")]},
    {"theme": "cosmic-hunt", "title": "Cosmic hunt (origin of constellations)", "confidence": "high",
     "note": "Hunters and their quarry are placed in the sky as a constellation "
             "(Ursa Major, Orion, the Pleiades). Berezkin's 'Cosmic hunt' cluster ↔ "
             "TMI's 'Origin of the Great Bear / Orion / Pleiades' — one Berezkin motif "
             "spans a whole TMI A77x sub-tree.",
     "members": [("berezkin", "B42"), ("berezkin", "B42B"), ("berezkin", "B42C"),
                 ("berezkin", "B42D"), ("berezkin", "B42E"), ("berezkin", "B42H"),
                 ("tmi", "A766"), ("tmi", "A771"), ("tmi", "A772"), ("tmi", "A773")]},
    {"theme": "star-spouse", "title": "Star husband / star wife", "confidence": "high",
     "note": "A person wishes on a star and is carried to the sky to marry it. "
             "Berezkin K19A/K19B/K20 ↔ TMI 'Star-Husband' (A762.1) and the wish-realised "
             "tabu motifs (C15.1). Different wording, identical mytheme.",
     "members": [("berezkin", "K19A"), ("berezkin", "K19B"), ("berezkin", "K20"),
                 ("tmi", "A762.1"), ("tmi", "C15.1"), ("tmi", "C15.1.1"), ("tmi", "T111.2.1.1")]},
    {"theme": "theft-of-fire", "title": "Theft / origin of fire", "confidence": "high",
     "note": "Fire is stolen from its owner and brought to people, often by an animal. "
             "Berezkin 'Theft of fire' (with animal-thief variants) ↔ TMI A1415 'Theft "
             "of Fire'. No ATU tale type (Prometheus is not a folktale plot).",
     "members": [("berezkin", "D4A"), ("berezkin", "D4D"), ("berezkin", "D4H"), ("tmi", "A1415")]},
    {"theme": "theft-of-daylight", "title": "Theft / recovery of the daylight", "confidence": "medium",
     "note": "The sun/light is hidden or stolen and must be won back. Berezkin 'Raven "
             "hides the Sun' ↔ TMI 'Theft of Sun' / 'Theft of Light'. On the ATU side "
             "the plot survives as 328A* 'Three Brothers Steal Back the Sun, Moon, and "
             "Star' — a looser, tale-level echo.",
     "members": [("berezkin", "A13A"), ("tmi", "A721.1"), ("tmi", "A1411"), ("atu", "328A*")]},
    {"theme": "arrow-chain-ascent", "title": "Ascent to the sky on an arrow-chain", "confidence": "high",
     "note": "Arrows shot into the sky lodge into a chain/ladder climbed to the upper "
             "world. Berezkin 'The arrow ladder' / 'Bridge of arrows' ↔ TMI F53 'Ascent "
             "to Upper World on Arrow Chain' and D469.3.",
     "members": [("berezkin", "J58"), ("berezkin", "J58C"), ("tmi", "F53"), ("tmi", "D469.3")]},
    {"theme": "sun-moon-siblings", "title": "Sun and Moon as siblings; the Moon's spots", "confidence": "medium",
     "note": "Sun and Moon are kin (often incestuous siblings), which explains the "
             "marks on the Moon's face. Berezkin 'The incestuous Moon' / 'Scars on the "
             "Moon's face' ↔ TMI 'Sun and Moon as Brothers' and 'Man in the Moon' (the "
             "spots). A many-to-many thematic cluster.",
     "members": [("berezkin", "A31"), ("berezkin", "A35C"), ("tmi", "A736.3"), ("tmi", "A751")]},
    {"theme": "death-false-message", "title": "Origin of death from a falsified message", "confidence": "high",
     "note": "The creator's message granting immortality is garbled by the messenger, "
             "so people become mortal. Berezkin H36A ↔ TMI A1335.1 (near-identical wording, "
             "the lexical pass catches this leg). ATU 934H 'The Origin of Death' is the "
             "novelistic reflex — a weaker, tale-level parallel.",
     "members": [("berezkin", "H36A"), ("tmi", "A1335.1"), ("tmi", "A1335.1.1"), ("atu", "934H")]},
    {"theme": "vagina-dentata", "title": "Vagina dentata", "confidence": "high",
     "note": "A woman's toothed vagina, later broken/de-fanged. Berezkin F9A ↔ TMI "
             "F547.1.1 'Vagina Dentata' and A1313.3.1 'Vaginal Teeth Broken'.",
     "members": [("berezkin", "F9A"), ("tmi", "F547.1.1"), ("tmi", "A1313.3.1")]},
    {"theme": "dual-creators", "title": "Dualism: two / hostile creators", "confidence": "medium",
     "note": "Two creators (one good, one spoiling) shape the world, often as rival or "
             "hostile brothers. Berezkin 'One creator deceives another' / 'Two creators: "
             "a dialogue' ↔ TMI 'Conflict of Good and Evil Creators' (A50), 'Two Creators' "
             "(A902.1), 'Hostile Brothers' (P251.5.3).",
     "members": [("berezkin", "B1C"), ("berezkin", "B5A"), ("tmi", "A50"),
                 ("tmi", "A902.1"), ("tmi", "P251.5.3")]},
    {"theme": "cosmic-egg", "title": "Cosmic egg", "confidence": "high",
     "note": "The world (or heaven and earth) hatches from a primordial egg. Berezkin "
             "'Cosmic egg' ↔ TMI A641 'Cosmic Egg' / A641.1 'Heaven and Earth from Egg'.",
     "members": [("berezkin", "B79"), ("tmi", "A641"), ("tmi", "A641.1")]},
    {"theme": "deluge", "title": "The deluge", "confidence": "medium",
     "note": "A world flood; survivors escape by boat, and its waters shape the "
             "landscape. Berezkin's many flood motifs (e.g. 'Waters of deluge create the "
             "mountains', 'Deluge and conflagration combined') ↔ TMI A1010 'Deluge' and "
             "A1021 'Deluge: Escape in Boat (Ark)'. Representative ids only — Berezkin's "
             "B-chapter flood set is large.",
     "members": [("berezkin", "B52"), ("berezkin", "C2"), ("tmi", "A1010"), ("tmi", "A1021")]},

    # --- Tale-type-anchored motifs (three-way: Berezkin ↔ TMI ↔ ATU) ---
    {"theme": "magic-flight", "title": "Magic flight / obstacle flight", "confidence": "high",
     "note": "Fugitives throw objects behind them that turn into obstacles (mountain, "
             "forest, sea) delaying the pursuer. The cleanest three-way parallel: "
             "Berezkin 'The obstacle flight' (with thrown-object sub-motifs) ↔ TMI "
             "D670/D672 ↔ ATU 313 'The Magic Flight'.",
     "members": [("berezkin", "L72"), ("berezkin", "L72C"), ("berezkin", "L72D"),
                 ("berezkin", "L72G"), ("tmi", "D670"), ("tmi", "D672"), ("atu", "313")]},
    {"theme": "swan-maiden", "title": "Swan maiden / the lost supernatural wife", "confidence": "high",
     "note": "A man steals a bird-woman's feather garment to marry her; she recovers it "
             "and flies away, and he must quest to regain her. Berezkin 'Swan-wife' / "
             "'Two brothers and the swan-maidens' ↔ TMI D361.1 'Swan Maiden' / B652.1 ↔ "
             "ATU 400 'The Man on a Quest for his Lost Wife'.",
     "members": [("berezkin", "E9i1"), ("berezkin", "K25a5"), ("tmi", "D361.1"),
                 ("tmi", "B652.1"), ("atu", "400")]},
    {"theme": "dragon-slayer", "title": "The dragon-slayer", "confidence": "high",
     "note": "A hero kills a dragon to rescue a princess (tongue-proof, impostor). "
             "Berezkin 'The dragon-slayer' ↔ TMI B11.11 'Fight with Dragon' ↔ ATU 300 "
             "'The Dragon-Slayer'.",
     "members": [("berezkin", "K38F"), ("tmi", "B11.11"), ("tmi", "B11.11.7"), ("atu", "300")]},
    {"theme": "blinded-ogre", "title": "Blinding the ogre (Polyphemus)", "confidence": "high",
     "note": "A captive blinds a man-eating giant and escapes hidden under a ram's "
             "belly. Berezkin 'Escape from Polyphemos' cave' / 'Blinded cyclopes' ↔ TMI "
             "G511 'Ogre Blinded' + K603 'Escape Under Ram's Belly' ↔ ATU 1137 'The "
             "Blinded Ogre'. Fully missed by the lexical pass (no shared words).",
     "members": [("berezkin", "K64"), ("berezkin", "K64a"), ("tmi", "G511"),
                 ("tmi", "K603"), ("tmi", "G121"), ("atu", "1137")]},
    {"theme": "nightingale-blindworm", "title": "The nightingale and the blindworm", "confidence": "high",
     "note": "The nightingale borrows the blindworm's eye and never returns it. Berezkin "
             "B125A ↔ TMI A2241.5 ↔ ATU 234 — an etiological tale present in all three "
             "(the lexical pass also caught the Berezkin↔ATU leg).",
     "members": [("berezkin", "B125A"), ("tmi", "A2241.5"), ("atu", "234")]},
]


def adjacency() -> dict[str, dict[str, list[int]]]:
    """Map each member motif to the indices of the groups it belongs to."""
    adj: dict[str, dict[str, list[int]]] = {"berezkin": {}, "tmi": {}, "atu": {}}
    for gi, g in enumerate(GROUPS):
        for index, mid in g["members"]:
            adj[index].setdefault(mid, []).append(gi)
    return adj
