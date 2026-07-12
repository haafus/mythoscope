# 51 · Descent / Diffusion / Invention

Answers the sharp question: **how do we tell a dispersed motif (low NRI) apart from late wide diffusion?**
Short answer — you can't from dispersal alone; a widely-spread motif can be deep **descent** (inherited,
differentially lost → relict/disjunct), late **diffusion** (borrowed along a contact corridor → contiguous,
corridor-confined), or independent **invention** (a cognitively obvious motif reinvented → simple,
observational). This is the anthropological trichotomy the earlier "deep substrate" framing glossed over.

## The method — stack the discriminators, add complexity

Two axes per motif (dispersed motifs, span ≥ 5 macro-areas):

- **x = complexity** — distinct content-words in the motif's definition. The classic
  transmission-vs-invention test: a **complex, arbitrary** motif is not reinvented twice, so its spread means
  it was *transmitted*; a **simple, observational** one could arise anywhere. (New signal; the rest reuse the
  project.) ATU tale-types are forced out of "invention" (they are complex by construction).
- **y = descent evidence** — **barrier-crossing** (the one hard test: diffusion *cannot* cross a barrier
  closed at a known date — mockup 49) + **geographic disjunction** (relict pockets, not a wave — M17
  fragments) + **independent early attestation** across disconnected dated corpora (mockup 50).

Modes: **Invention-prone** = simple + observational (spread ≠ transmission). Otherwise transmitted →
**Descent** if barrier/disjunction/attestation is strong, **Diffusion** if corridor-confined and contiguous
with none of it, else **Ambiguous**.

## What it shows (1477 dispersed motifs)

- **Descent 622 · Diffusion 378 · Invention-prone 357 · Ambiguous 120.** Diffusion picks out exactly the
  complex Old-World-corridor märchen (*Precious advices, Baby child substituted, Secrets accidentally
  overheard, The impossible giving birth*); descent picks the complex cosmological motifs that cross barriers
  and recur in many corpora (*Eclipses: monster's attack, The collapse of the sky, Deluge and conflagration*).
- **The irreducible ambiguity — the real answer.** **307 of the 357** invention-prone motifs are *also* old
  (barrier-crossing or documented in ≥ 2 disconnected corpora): the celestial/cosmogonic core — *Male sun and
  female moon, Primeval waters, Figure on lunar disc, The Sun and the Moon are males*. They are ancient **and**
  simple **and** observational, so their pan-global spread **cannot** distinguish deep common descent from
  ancient independent invention (psychic unity). **A large part of the "deep substrate" is mode-undecidable** —
  which honestly qualifies the mockup-48/49 substrate story.

## Honest limits

The complexity axis is a **text proxy** (definition content-words) — it undersells a narratively complex motif
with a terse definition and no ATU tag (*Magic wife* / swan-maiden, a known *transmitted* tale, slips into
"invention-prone"). The descent axis rests on barrier-crossing (hard, but can't exclude independent invention
on both sides). Read the four modes as **weight of evidence, not verdicts**. Relation to prior work: this is a
*synthesis* — it reuses M17 disjunction, mockup-49 barriers and mockup-50 corpora — plus the one genuinely new
signal (definition complexity) and the three-way classifier no earlier mockup drew.

## Data

`build_data.py`: per motif — macro-area span, geographic fragments (DBSCAN), barrier tier, disconnected
dated-corpus count, definition content-word complexity, etiological/ATU flags → the two axes and the mode.
Deterministic; writes `data.js`.

## Run

```bash
python mockups/51-descent-diffusion-invention/build_data.py    # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/51-descent-diffusion-invention/
```
