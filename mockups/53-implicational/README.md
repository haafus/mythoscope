# 53 · Implicational structure

Asymmetric co-occurrence as a **data-driven motif taxonomy** (analysis #6). If a tradition has motif **X** it
almost always has motif **Y** but not the reverse (P(Y|X) ≥ 0.80 ≫ P(X|Y), X rarer) → **X implies Y**, i.e. X is
a **specialization** of Y.

**Finding.** Over 1390 frequent motifs, ~10k strong implications, which read as **"is a kind of"** and recover a
**subtype → type** hierarchy the flat `motif_group` can't express. The **type hubs** are the big complexes —
*Trickster-fox*, *Magic wife*, *Task-giver is a king*, *The false wife*, *The external soul*, *The dragon-slayer*
— each with the specific variants that entail it (*Duck-wife ⇒ Magic wife*, *Puss-in-Boots ⇒ Trickster-fox*).
**Cross-theme implications** (X and Y in different theme groups) are the non-obvious ones. A first data-derived
motif ontology over Berezkin's flat groups.

`build_data.py` computes pairwise conditional probabilities over motifs attested in ≥25 traditions, keeps
asymmetric high-confidence implications, and groups them by implied hub; writes `data.js`.
