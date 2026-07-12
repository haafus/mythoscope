# 50 · Dated attestations

Real **calendar-year** floors with no external file — the textual *terminus ante quem* route from
[`../../docs/research/dating-and-chronology-methods.md`](../../docs/research/dating-and-chronology-methods.md)
(method A-5), plus the "datings of known religions" idea. The trick: several of Berezkin's own traditions
*are* dated literate corpora, so a motif recorded in one is **documented by** that corpus's date.

## The dated corpora

15 curated traditions, each a dated corpus with a confidence tag and a span note (lumped corpora over-state
the old end — flagged):

| | terminus ante quem | | | terminus ante quem |
|---|---|---|---|---|
| Ancient Egypt | ~2350 BCE | | Iranian / Avesta | ~1000 BCE |
| Sumer | ~2100 BCE | | Phoenicia | ~900 BCE |
| Akkad / Babylon | ~1700 BCE | | Ancient Italy | ~600 BCE |
| Hittite | ~1400 BCE | | Greek (on India) | ~300 BCE |
| Ugarit | ~1300 BCE | | Maya | ~250 CE |
| Vedic / Indian | ~1200 BCE¹ | | Japan (Kojiki) | 712 CE |
| Early Chinese | ~1000 BCE | | Arab (1001 Nights) | ~950 CE |
| | | | Aztec | ~1400 CE |

¹ Rigveda ~1500 BCE but the tradition lumps Puranas (~1000 CE) — the old bound is optimistic.
**"Koreans; Goguryeo" is deliberately excluded** — its corpus is dominantly modern folklore, so a Goguryeo
(~400 CE) date would falsely age it. This is the central hazard: a documented floor is only as reliable as
the corpus is tightly dated.

## What it shows

- **Coverage.** Textual attestation floors **707 motifs** — **329 of them not reachable by any
  biogeographic barrier** (mockup 49), lifting the total with an absolute floor from 1284 to **1613**. Texts
  reach the literate Old-World fraction that barriers miss.
- **Corpus timeline.** When each motif-complex first enters the written record, Egypt (2350 BCE) → Aztec
  (1400 CE), point size = motifs *first* documented there.
- **Oldest documented motifs.** The first written myths are the celestial/cosmogonic substrate — *Primeval
  sky close to earth, The Sun and the Moon are males, Eclipses: monster's attack, Marriage of sky and earth,
  Primeval waters* — attested in Egypt 2350 BCE and, for many, independently across up to **9 dated corpora**.
- **Independently documented across ≥4 corpora.** *The female earth* (9 corpora), *Primeval sky* (8),
  *Sun & Moon are males* (7): recorded separately in Egypt *and* Sumer *and* China *and* Mesoamerica — hard,
  redundant evidence of antiquity, the deep substrate seen from the written side. Cross-reads with the
  mockup-48 teleconnectors and the mockup-49 barrier floors.

## The honest result

**Documented age does not track distributional depth.** Mean M17 depth is flat across documented-age buckets
(57 / 64 / 57) and the rank correlation is only **0.02**. They are **independent, confounded signals**:
textual floors favour cultures that *wrote* — a genuinely ancient Americas-only motif gets no floor while a
younger Sumerian one does. So this is a layer of **hard calendar anchors** (real BCE dates, ideal for
calibrating/validating other methods), **not** a universal clock — and it is exactly the literacy bias the
research note warned about, made visible.

## Data

`build_data.py`: maps each motif to the dated corpora attesting it → an oldest-attestation floor; recomputes
the biogeographic barrier floors and the M17 depth proxy; emits coverage, the corpus timeline, the
earliest-attestation histogram, the oldest / multi-corpus motif lists, and the depth-by-age validation.
Deterministic; writes `data.js`.

## Run

```bash
python mockups/50-dated-attestations/build_data.py    # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/50-dated-attestations/
```
