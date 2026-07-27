# Figma `MythoSemantic` — extracted public-site copy (raw source)

Verbatim text extracted from the Figma file `MythoSemantic`
(`figma.com/design/55OAEefLJl5nxXs5FzZxjy/`) via the REST API on 2026-07-27. This is the
**raw source copy** for the public documentation section — see
[`public-docs-plan.md`](public-docs-plan.md) §14 for how each block maps onto the plan's
sections and how to treat it (adopt / translate / keep-internal).

Notes:
- Preserved here so it survives the ephemeral container. No Figma token is stored.
- Some blocks are **Russian internal strategy memos** (addressed to "ты" — notes to the
  founder). They are kept for provenance but are **not public copy**; adapt the ideas, do not
  publish verbatim.
- The file also contained a Bhagavad-Gita excerpt and tradition-metadata JSON — those are
  mockup *sample data*, not copy, and are omitted (only summarised at the end).

---

## 1. Vision / pitch (EN — near-ready)

> The first large-scale infrastructure for comparative analysis of mythology, religion, and
> ancient literature — an international collaborative project integrating classical
> interpretive methods with artificial intelligence to investigate shared origins and deep
> structural patterns of human culture.
>
> Mythoscope is an interdisciplinary research initiative and open analytical platform
> dedicated to the large-scale comparative study of mythology, ancient religions, and cultural
> texts. Integrating classical humanities methodologies with computational approaches, the
> project enables scholars to explore deep semantic structures, trace cultural patterns across
> traditions, and investigate the historical evolution of symbolic systems.
>
> **Toward a Computational Framework for Comparative Mythology.** The framework enables
> large-scale, cross-cultural, reproducible analysis, combining unsupervised (bottom-up,
> continuous) and supervised (top-down, discrete) methods to provide a foundation for future
> work in computational mythology and digital humanities.

Tagline / brand line: **Mythoscope — Collaborative Semantic Archaeology.**

Additional framing fragments:
- "Telescope, Microscope, Spectroscope… new lens and reinvention"
- "large corpora + ml/ai methods + humanities + collaboration"

Three-layer model (level of a large research initiative):
- **Conceptual layer** — semantic archaeology (the project's philosophy)
- **Methodological layer** — computational framework (the paper)
- **Infrastructural layer** — Mythoscope (the collaborative platform)

Situated at the intersection of: antiquity (myth, archaeology, heritage) · modern science
(AI, digital humanities, infrastructure) · collectivity (international collaboration,
openness).

---

## 2. Manifesto — "Why Collaborative Infrastructure for Theory Discovery?" (EN)

> **1. Scale reveals what examples hide**
> Lévi-Strauss analyzed dozens of myths · Campbell analyzed hundreds · We'll analyze tens of
> thousands. Different scale = different patterns visible.
>
> **2. Algorithms see what humans can't**
> Humans notice explicit similarities · Algorithms detect latent semantic patterns ·
> Clustering reveals hidden groupings · Computational methods complement human interpretation.
>
> **3. Collaboration transcends individual bias**
> Every scholar has theoretical commitments · Single perspectives miss cultural specifics ·
> Distributed expertise provides triangulation · Community knowledge exceeds individual
> knowledge.
>
> **4. Open infrastructure outlives individual projects**
> Theories come and go · Infrastructure persists · Enables future researchers to ask new
> questions · Tools for discovery, not just verification.

Deductive → inductive contrast (diagram copy):

> **Traditional comparative mythology:** Scholar → Limited corpus → Theory
> (deductive: test hypothesis on examples).
> **Mythoscope approach:** Global corpus → Computational analysis → Patterns emerge →
> Community interpretation → Theory generation (inductive: discover patterns, then interpret).

> "We don't know the answers. Let's build a tool to find them."
> "Applying computational methods to comparative mythology."
>
> MYTHOSCOPE is research infrastructure designed for **discovery, not verification**. By
> combining collaborative corpus building (thousands of texts from specialists worldwide),
> computational pattern discovery (unsupervised ML reveals latent structures), and community
> interpretation (distributed expertise validates and contextualizes findings)… we enable
> patterns to emerge from data that no single scholar could analyze. Our goal isn't to prove
> existing theories. It's to discover new ones.

> "Individual scholars propose theories. Communities discover truth."

*(See plan §14.1: reconcile "discovery, not verification / we don't know" with the Element's
results-first, honest register before publishing.)*

---

## 3. Name essay — the `-scope` epistemic lens (RU — INTERNAL memo, translate to publish)

> Слово Mythoscope действительно несёт скрытую историческую ассоциацию… В англоязычной научной
> культуре суффикс -scope — это не просто «прибор», а символ определённого эпистемического
> поворота XIX века, когда знание стало производиться через инструменты наблюдения: microscope,
> telescope, spectroscope, oscilloscope. Эти названия исторически связаны с моментом, когда
> наука начала открывать невидимые уровни реальности — микромир, космос, спектры, электрические
> сигналы.
>
> Когда гуманитарная аудитория слышит Mythoscope, даже неосознанно возникает аналогия:
> «инструмент, который делает видимым то, что раньше было скрыто в текстах и традициях». Это
> переводит исследование мифологии из области описательной дисциплины в область инструментального
> знания — почти как если бы мифология получила собственный «микроскоп».
>
> Для digital humanities и AI-сообщества это звучит особенно убедительно… telescope изменил
> астрономию, microscope изменил биологию, а значит Mythoscope подразумевает новую фазу
> исследований культуры. Такое название создаёт ощущение методологического скачка.
>
> [STS/философия] суффикс -scope ассоциируется с идеей опосредованного наблюдения. После работ
> Фуко, Латура, Харэуэй и STS-традиции инструмент не просто показывает реальность, он формирует
> способ её видеть → «миф как наблюдаемая система смыслов». Язык «epistemic instruments» и
> «conceptual lenses»; перекличка с герменевтикой (Рикёр, Кассирер) — герменевтика как оптика.
> Подзаголовок Semantic Archaeology удерживает связь с философской традицией и предотвращает
> впечатление чисто технократического проекта.

*(Two RU variants of this essay existed in the file; condensed to the load-bearing points.
Publish as an English "Why 'Mythoscope'?" note on the About page.)*

---

## 4. Methodology / DH notes (RU + mixed — mark aspirational vs. implemented)

Methods brainstorm:

> Эмбеддинги локальных чанков (несколько ступеней размера) · эмбеддинги генеративных
> суммаризаций · иерархическая суммаризация? · графы отношений/времени/пространства · topic
> modeling · motif keywords / semantic fields · narrative-arc embeddings? · triplet/contrastive
> · fulltext search · fulltext template search · concordance · use embedding instructions ·
> семантические поля слов и их сети.

Embeddings as **interpretive operators** (the key idea):

> Не «найди похожие документы», а: «смотри на текст как структуралист / психоаналитик /
> системный теоретик». Фактически превращать embedding model в набор интерпретативных
> операторов: пропповский · леви-строссовский · юнгианский · ритуально-антропологический.
> (Герменевтика: Шлейермахер, Дильтей, Гадамер, Хайдеггер, Рикёр, Деррида.)

Unit of comparison & the 3-level similarity:

> Единица сравнения — не весь текст, а уровни: motif · image · narrative function · mythic
> actor · cosmological structure · ritual formula · speech act · temporal pattern · spatial
> structure · theological relation.
>
> Для каждого совпадения разделять 3 уровня сходства:
> `{ "SimilarityLevel": { "Lexical": false, "Imagistic": true, "Structural": true } }`
> — одинаковые слова ≠ одинаковый мотив; одинаковый мотив ≠ одинаковая структура; структура
> может совпадать без общих образов.
>
> Обязательно выделять **narrative function**. Напр. вода: origin · boundary · punishment ·
> purification · passage — без функции «вода везде кажется одинаковой».

Scalable reading / computational hermeneutics:

> Close reading ↔ scalable reading практически совпадает с классической сравнительной
> мифологией: алгоритм выделяет кластеры сюжетов → исследователь выбирает ключевые эпизоды →
> обновляет модель. Digital Humanities — не data science для текстов, а новая герменевтическая
> дисциплина. Термины: computational mythology, computational hermeneutics, LLM-assisted
> hermeneutics.

The "big questions":

> Какие виды мировоззрений, ценностных ориентаций и психотехнологий существовали в прошлом? Как
> они изменялись, переносились, взаимодействовали? Какие нейрофизиологические/психологические
> основания их формируют? Что остаётся за пределами объяснения? — Каково человеческое
> разнообразие / эволюция / природа? Что остаётся непознанным?

---

## 5. Contribute — "JOIN THE COLLABORATION" (EN — adopt as C1 backbone)

> **JOIN THE COLLABORATION — Build the Infrastructure for Discovering Deep Patterns in Human
> Culture.** MYTHOSCOPE is not a project—it's collaborative infrastructure being built by a
> global community of scholars, technologists, and culture specialists. We need your expertise,
> your collections, your methods, your questions. We don't know what we'll discover. That's why
> we need diverse perspectives, comprehensive data, and innovative approaches.

**How to collaborate** (each with *what we need / what you gain / ideal for / get started*):

- 📚 **Contribute corpora & texts** — mythological texts from any tradition; vetted
  translations & critical editions; rare/understudied traditions; regional variants & oral
  traditions; sacred narratives (with permissions). *Ideal for:* philologists, folklorists,
  anthropologists, religious-studies scholars, curators, librarians, Indigenous knowledge
  keepers.
- 🏷️ **Provide metadata & annotations** — structured metadata; expert annotations (motifs,
  themes, characters); cultural context; linguistic markup; variant tracking. *Ideal for:*
  area-studies specialists, linguists, cultural historians, graduate students.
- 🗺️ **Contribute non-textual datasets** — geographic (origins, transmission routes), temporal
  (dating), archaeological correlates, iconographic databases, audio (oral traditions), network
  data (contact, trade). *Ideal for:* archaeologists, art historians, ethnomusicologists,
  geographers, digital archivists.
- 🔬 **Develop & refine methods** — NLP for ancient languages, clustering, network analysis,
  visualization, multilingual embeddings, evaluation metrics. *Ideal for:* computer scientists,
  computational linguists, data scientists, DH methodologists.
- 🔍 **Validate discoveries & co-author publications** — expert interpretation of computational
  findings, cultural context, critical evaluation, alternative explanations, theory. *Ideal
  for:* senior scholars, theorists, comparative-literature specialists.
- 💰 **Support through funding** — grant partnerships, institutional sponsorship, foundation
  connections, donations, in-kind (computing, personnel).
- 💻 **Contribute code & infrastructure** — platform (Python, React, databases), cloud, API,
  security/auth, visualization, mobile, DevOps. *Ideal for:* software engineers, web devs,
  DevOps, UX designers, CS students.
- 🏛️ **Institutional partnerships** — departments/centers, institutes, museums, libraries &
  archives, DH initiatives, international networks.
- 📰 **Media, outreach & publicity** — science communication, documentary/video, podcasts,
  social amplification, public lectures, educational content, translation/localization.
- 🎓 **Educational collaborations** — course development, student supervision, workshops/summer
  schools, tutorials, training materials, citizen science.
- 🌍 **Indigenous knowledge & community partnerships** (with full respect & consent) — cultural
  protocols, community-curated representations, oral recordings where appropriate, review of
  interpretations, co-governance. *We offer:* full control, CARE-principles compliance, proper
  attribution, community benefit sharing, removal rights.
- 🧪 **Postdoctoral & student opportunities** — fellowships (subject to funding), assistantships,
  internships, thesis projects, publications. *(Keep internal until funded.)*
- 💬 **Join the conversation** — discuss methodology, debate frameworks, suggest directions.
  *Forums:* monthly community calls, Slack, GitHub Discussions, annual conference, working
  groups.
- 🤝 **Other collaborations** — novel partnership models, cross-disciplinary experiments,
  unexpected applications.

**Collaboration principles:** ✅ Open Science (all contributions credited, outputs open access)
· ✅ Equity (Global-South scholars, ECRs, underrepresented voices prioritized) · ✅ Attribution ·
✅ Transparency · ✅ Respect (cultural protocols, Indigenous sovereignty) · ✅ Quality (peer
review & validation) · ✅ Sustainability (building for decades, not years).

**Start today:** Explore the platform → choose your contribution → reach out.

> "This is infrastructure for collective discovery. No single scholar, institution, or nation
> can answer fundamental questions about human mythology alone… We can discover what none of us
> could find alone. That's why this is collaborative. That's why we need you."

*Placeholder contact addresses in the source (`corpora@`, `metadata@`, `datasets@`, `methods@`,
`research@`, `funding@`, `tech@`, `partnerships@`, `press@`, `education@`, `indigenous@`,
`careers@`, `community@`, `collaborate@`, `contact@` `mythoscope.org`) — **do not publish until
the mailboxes exist**; collapse to one or two real addresses.*

---

## 6. Proposed sitemap (from the mockup — reconcile with plan §9)

```
mythoscope.org/
├── Home (Hero + Overview)
├── About        (The Project · Methodology · Team · Partners)
├── Explore      (Search Corpus · Browse by Culture · Browse by Motif · Visualizations)
├── Research     (Publications · Case Studies · Documentation · API)
├── Contribute   (Add Corpus · Annotate · Join Team · Guidelines)
├── Learn        (Tutorials · Workshops · Resources)
└── News & Events
```

Their **Explore** = our SPA app (Sources/Similarity/Atlas/Motifs); their **Learn** = net-new
tutorials; **Team/Partners** = keep internal until real.

---

## 7. Resources — digital text libraries (adopt into C2 / dedupe with B4)

Perseus Digital Library · Sacred Texts Archive · Electronic Text Corpus of Sumerian Literature
(ETCSL) · Thesaurus Linguae Aegyptiae · Sanskrit Library · GRETIL (Göttingen Register of
Electronic Texts in Indian Languages) · Chinese Text Project · National Institute of Japanese
Literature database · Internet Archive · Project Gutenberg · HathiTrust · Fordham Internet
History Sourcebooks · Open Islamicate Texts Initiative (OpenITI) · TITUS Project · Finnish
Literature Society (SKS) folklore archive · American Folklife Center (Library of Congress) ·
World Oral Literature Project · Native American Ethnography database (Alexander Street) ·
Polynesian Texts Collection (Univ. of Auckland) · Buddhist Digital Resource Center.

---

## 8. Related work (RU — already covered by the research surveys, dedupe into B3)

- **GOLEM** (Yarlott et al., LREC-COLING 2024) — gold-standard motif corpus (26k candidates, 34
  motif types); LLMs reach only 41% accuracy → very hard task.
- **Automated Motif Indexing on Arabian Nights** (Alyami & Finlayson, 2026) — auto TMI tagging
  via embedding + re-ranking.
- **Cinderella Case Study** (Arcon et al., 2025) — LLM motif detection across Cinderella
  variants + clustering + dimensionality reduction.
- **Annotated Folktales** (Hagedorn & Daranyi, 2022) — open ATU-annotated corpus; SVM F1 0.8–1.0.
- **BERT encodes narrative dimensions** (Bei et al., CMN 2026) — linear probe 94% for time,
  space, causality, characters.
- **Story Embeddings** (Hatzel & Biemann, EMNLP 2024) — most relevant; fine-tuned
  `intfloat/e5-mistral-7b-instruct` with LoRA on original–retelling pairs so plot-similar (not
  style-similar) texts cluster; model: `uhhlt/story-emb`.

---

## 9. UI / nav / footer strings (confirms plan §9–§10)

- **Site nav (mockup):** About · Sources / Corpora · Semantics · Relations / Structure ·
  Concordance / Search · Geo / Map · Literature / Books · Publications · Links / Resources ·
  Take part! / Contribute.
- **App nav (mockup):** Sources · Similarity · Ages · Realms · Beings · Geography.
- **Footer social set:** X · Substack · YouTube · Discord · GitHub · Email.
- **Wordmark / strapline:** MYTHOSCOPE · "COLLABORATIVE SEMANTIC ARCHÆOLOGY".
- **Proposed tradition taxonomy** (side menu), grouped: Indo-European (Vedic — RgVeda,
  SamaVeda, YajurVeda, AtharvaVeda; Hindu — Bhagavad Gita, Ramayana, Upanishads; Iranian, Greek,
  Roman, Germanic, Norse, Celtic, Baltic, Slavic) · Near East (Egyptian; Judaism — Torah,
  Talmud, Midrash, Mishnah; Christianity; Sumerian, Akkadian, Assyrian, Hittite, Hurrian,
  Canaanite, Ugaritic, Phoenician) · South & Southeast Asia (Dravidian, Buddhist, Jain, Thai,
  Khmer, Indonesian, Filipino) · East Asia (Tibetan, Chinese, Japanese, Korean) · Central Asia &
  Circumpolar (Turkic, Mongolian, Siberian, Sami, Chukchi, Yupik) · Africa (Berber, Yoruba,
  Akan, Dogon, Dinka, Zulu, Maasai) · North America (Inuit, Algonquian, Iroquois, Navajo,
  Pueblo, Lakota) · Mesoamerica (Maya, Aztec, Mixtec, Zapotec) · South America (Inca, Quechua,
  Aymara, Guarani, Amazonian) · Oceania & Australia (Polynesian, Micronesian, Melanesian,
  Australian).

---

## 10. Omitted mockup sample data (for the record)

The file also carried, as illustrative placeholder content: a long **Bhagavad-Gita, Chapter I**
excerpt (Arnold translation) shown in a reader frame, and small **tradition-metadata JSON**
snippets for Greek / Norse / Vedic (fields `tradition`, `language_family`, `approx_recorded`,
`location`, `coordinates`, `major_texts`). These are sample data, not site copy, and are not
reproduced here.
