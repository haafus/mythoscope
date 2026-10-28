import { api, app, formatNumber } from "./core.js";

const REPO = "https://github.com/haafus/mythoscope";
const AWESOME = "https://github.com/haafus/awesome-computational-mythology";
const PREPRINT = "https://arxiv.org/abs/2610.28452";
const EMAIL = "hello@mythoscope.io";

export function renderAbout() {
    app.innerHTML = `
        <main class="about-page">
            <div class="header-container">
                <img src="/assets/logo.jpg" alt="Mythoscope Logo" class="logo-image">

                <nav class="nav-menu">
                    <button class="nav-item active" type="button" data-tab="vision">Vision</button>
                    <span class="separator">|</span>
                    <button class="nav-item" type="button" data-tab="methodology">Methodology</button>
                    <span class="separator">|</span>
                    <button class="nav-item" type="button" data-tab="contribute">Contribute</button>
                    <span class="separator">|</span>
                    <button class="nav-item" type="button" data-tab="resources">Resources</button>
                </nav>
            </div>

            <div class="content-container">
                <div id="vision" class="tab-content active">
                    <p class="about-lead">An open, collaborative infrastructure for the comparative study of mythology, religion and ancient literature, integrating established interpretive methods with artificial intelligence.</p>
                    <p>Mythoscope is an interdisciplinary research initiative and open analytical platform. It combines unsupervised (bottom-up, continuous) and supervised (top-down, discrete) methods so that scholars can explore semantic structure across traditions, trace cultural patterns and test them reproducibly, at a scale no single reader can reach.</p>

                    <dl class="about-stats" hidden></dl>

                    <h3>Why</h3>
                    <ol class="about-points">
                        <li><strong>Reading has limits.</strong> No scholar can read and compare thousands of texts, and a hand-picked sample, shaped by one perspective, can't be redrawn or tested.</li>
                        <li><strong>Indexes inherit these limits.</strong> They are hand-compiled, centred on Europe and Western Asia, and detached from the texts and from each other.</li>
                        <li><strong>Expertise is fragmented.</strong> Specialists know one tradition deeply, rarely several, and corpora are scattered.</li>
                        <li><strong>Computation opens a new scale.</strong> NLP and AI make it possible to look for motifs in the texts themselves, across the whole corpus and many traditions at once.</li>
                        <li><strong>The work is too big for one team.</strong> Corpora, methods and infrastructure need specialists from many fields, so the project is open and collaborative.</li>
                    </ol>

                    <h3>Publication</h3>
                    <p class="about-ref">Ganziuk, N., Humonen, I. S., Makarov, I., &amp; Lebedev, P. (2026). <a href="${PREPRINT}" target="_blank" rel="noopener"><em>MythoSemantic: An Interactive System for Discovering Semantic Parallels Across Mythological and Religious Traditions</em></a>. arXiv:2610.28452 [cs.CL], preprint. Describes the semantic-space baseline behind the Similarity view.</p>

                    <h3>Status</h3>
                    <p>Mythoscope is early-stage, actively developed research software. The application is live and its code is open on <a href="${REPO}" target="_blank" rel="noopener">GitHub</a>; results so far are exploratory and are documented together with their data, method and limitations.</p>
                </div>

                <div id="methodology" class="tab-content">
                    <h3>Two layers of data</h3>
                    <p><strong>A text corpus.</strong> Primary texts of mythological and religious traditions from open sources, split into overlapping fragments and embedded in one semantic space. Every source sits in a hierarchy (macro-region › culture › text) that drives browsing, filtering and aggregate statistics.</p>
                    <p><strong>Three folklore indexes.</strong> Thompson's <em>Motif-Index of Folk-Literature</em> (TMI), the Aarne–Thompson–Uther tale-type index (ATU) and the Berezkin &amp; Duvakin analytical catalogue, cross-linked into one motif database. Links that come from the indexes themselves are kept separate from inferred links, which are marked by source and confidence.</p>

                    <h3>Pipeline</h3>
                    <p>Nine stages lead from raw sources to this interface. They are incremental: when a text is added or an algorithm changes, only the affected outputs are rebuilt, so the corpus can grow cumulatively.</p>
                    <div class="about-pipeline">
                        <div><h4>Data</h4><p>Scraping · Ingestion · Chunking</p></div>
                        <div><h4>Models</h4><p>Embedding · Dimensionality reduction · Graph extraction</p></div>
                        <div><h4>Serving</h4><p>Global statistics · Model management · UI server</p></div>
                    </div>

                    <h3>What you can do here</h3>
                    <ul class="about-list">
                        <li><a href="#/corpus"><strong>Sources</strong></a>: read the full texts, with size, description and the edition used.</li>
                        <li><a href="#/embeddings"><strong>Similarity</strong></a>: find a passage's nearest neighbours, optionally only in other traditions, or search by meaning; embedding models and projections (UMAP, t-SNE, PCA) can be switched.</li>
                        <li><a href="#/ages"><strong>Ages</strong></a>, <a href="#/realms"><strong>Realms</strong></a>, <a href="#/beings"><strong>Beings</strong></a>: times, places and characters with their relations, extracted from each text with a language model and linked to the passages they come from.</li>
                        <li><a href="#/motifs"><strong>Motifs</strong></a>: browse and search the three indexes by chapter, with statistics by region and culture and a page for every motif or tale type.</li>
                        <li><a href="#/geography"><strong>Atlas</strong></a>: see where each tradition sits on the map.</li>
                    </ul>

                    <h3>Principles</h3>
                    <ul class="about-list">
                        <li>Results are passages with provenance, not generated explanations.</li>
                        <li>Semantic parallels between motifs are hints for expert review, never presented as established links.</li>
                        <li>Uneven collecting is a known bias: how densely a tradition is catalogued is carried into the analyses rather than ignored.</li>
                        <li>Negative results are reported alongside positive ones. Example: the date of a motif's first written attestation does not predict how old its distribution suggests it is (rank correlation 0.02), because written records favour cultures that wrote; written dates are lower bounds, not a universal clock.</li>
                    </ul>

                    <h3>Known limits</h3>
                    <p>Inducing motifs directly from raw text is built as infrastructure but not yet validated at scale; the analyses run on the curated indexes. The indexes keep the geographic biases of their compilers, and tradition locations are the catalogue's own hand-placed markers, not survey-grade coordinates.</p>
                </div>

                <div id="contribute" class="tab-content">
                    <p class="about-lead">Mythoscope is open to collaboration with folklorists, specialists in individual traditions, computational linguists, ML engineers and developers.</p>

                    <h3>Ways to help</h3>
                    <ul class="about-list">
                        <li><strong>Texts and corpora</strong>: vetted translations and editions, especially from under-represented traditions, and sources in original languages.</li>
                        <li><strong>Expert review</strong>: corrections to the tradition taxonomy, to motif links and to cleaned texts; reporting what looks wrong is itself a contribution.</li>
                        <li><strong>Methods</strong>: motif induction from text and its evaluation against a gold standard, the principal open problem.</li>
                        <li><strong>Code and infrastructure</strong>: a Python pipeline (FastAPI, ChromaDB, UMAP) with a plain JavaScript interface; see the <a href="${REPO}/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">contributing guide</a>.</li>
                        <li><strong>Case studies</strong>: studies designed and checked together with specialists in individual traditions.</li>
                    </ul>

                    <h3>Credit</h3>
                    <p>Every contribution is credited, on a ladder that scales with the work: acknowledgement, then citation of a distinct dataset or tool, then co-authorship for substantial contributions. Roles follow the CRediT taxonomy, so it is explicit who did what. Material belonging to living communities is handled under the CARE principles for Indigenous data governance, including the right to review and to have material removed.</p>

                    <h3>What's ahead</h3>
                    <ol class="about-points">
                        <li><strong>Curating the corpus</strong>: more traditions, better balance, sources in original languages.</li>
                        <li><strong>Advancing the methods</strong>: motif induction from texts; representations built on character and relation graphs.</li>
                        <li><strong>Conducting studies</strong> with specialists in individual traditions.</li>
                        <li><strong>Scaling the infrastructure</strong>: versioned, archived releases with DOIs.</li>
                        <li><strong>Growing the community</strong>: credit for contributors, from acknowledgement to co-authorship.</li>
                    </ol>

                    <h3>Get in touch</h3>
                    <p>Open an issue or a pull request on <a href="${REPO}" target="_blank" rel="noopener">GitHub</a>, or write to <a href="mailto:${EMAIL}">${EMAIL}</a>.</p>
                </div>

                <div id="resources" class="tab-content">
                    <h3>For the field</h3>
                    <ul class="about-list">
                        <li><a href="${AWESOME}" target="_blank" rel="noopener"><strong>Awesome Computational Mythology</strong></a>: an open, curated list of indexes, datasets, corpora, methods, tools, papers, scholars and venues.</li>
                        <li><a href="${REPO}/tree/main/docs/research" target="_blank" rel="noopener"><strong>Survey of the field</strong></a>: computational work on myth and folklore, 2008–2026: methods and research groups, motif induction, dating methods and the available sources per tradition.</li>
                    </ul>

                    <h3>Data sources and licences</h3>
                    <p>Third-party texts and indexes keep their own terms, and their provenance travels with the data.</p>
                    <ul class="about-list">
                        <li><strong>Berezkin &amp; Duvakin</strong>, analytical catalogue of folklore and mythological motifs (<a href="http://areasofmyths.com" target="_blank" rel="noopener">areasofmyths.com</a>), CC BY-NC-SA 4.0.</li>
                        <li><strong>Thompson Motif-Index and ATU tale types</strong> via <a href="https://github.com/j-hagedorn/trilogy" target="_blank" rel="noopener">j-hagedorn/trilogy</a> (CC BY-SA 4.0) and Katja Mellmann's <a href="https://github.com/KatjaMellmann/TMI_as_CSV" target="_blank" rel="noopener">TMI_as_CSV</a> (CC BY 4.0).</li>
                        <li><strong>Texts</strong> from open digital libraries such as Project Gutenberg; each source in Sources links to the edition used.</li>
                    </ul>
                    <p>Mythoscope's own layers: code under MIT, documentation under CC BY-SA 4.0, derived datasets such as the motif crosswalk under CC BY 4.0 (<a href="${REPO}/blob/main/LICENSE" target="_blank" rel="noopener">LICENSE</a>).</p>

                    <h3>How to cite</h3>
                    <p>Until the first archived release receives a DOI, cite the preprint and name the version of the software you used.</p>
                    <pre class="about-cite">@misc{ganziuk2026mythosemantic,
  title         = {MythoSemantic: An Interactive System for Discovering Semantic Parallels Across Mythological and Religious Traditions},
  author        = {Ganziuk, Nikita and Humonen, Innokentiy S. and Makarov, Ilya and Lebedev, Pavel},
  year          = {2026},
  eprint        = {2610.28452},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL}
}</pre>
                </div>
            </div>

            <footer class="about-contact">
                <div><span class="about-contact-label">Author</span>Pavel Lebedev, independent researcher</div>
                <div><span class="about-contact-label">Contact</span><a href="mailto:${EMAIL}">${EMAIL}</a></div>
                <div><span class="about-contact-label">Code</span><a href="${REPO}" target="_blank" rel="noopener">github.com/haafus/mythoscope</a></div>
                <div><span class="about-contact-label">Preprint</span><a href="${PREPRINT}" target="_blank" rel="noopener">arXiv:2610.28452</a></div>
            </footer>
        </main>
    `;

    app.querySelectorAll(".nav-item").forEach((button) => {
        button.addEventListener("click", () => {
            app.querySelectorAll(".tab-content").forEach((content) => content.classList.remove("active"));
            app.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
            const target = document.getElementById(button.dataset.tab);
            if (target) target.classList.add("active");
            button.classList.add("active");
        });
    });

    renderStats(app.querySelector(".about-stats"));
}

// Counts come from the live API so the page never carries stale numbers; any
// endpoint that is unavailable (e.g. motifs not built) simply drops its figures.
async function renderStats(container) {
    const [documents, traditions, indexes] = await Promise.allSettled([
        api("/api/corpus/documents"),
        api("/api/corpus/traditions"),
        api("/api/motifs/indexes"),
    ]);
    const items = [];
    if (documents.status === "fulfilled") items.push([documents.value.total, "texts"]);
    if (traditions.status === "fulfilled") items.push([traditions.value.total, "traditions"]);
    if (indexes.status === "fulfilled") {
        const labels = { tmi: "Thompson motifs", atu: "ATU tale types", berezkin: "Berezkin motifs" };
        for (const index of ["tmi", "atu", "berezkin"]) {
            const entry = indexes.value.indexes.find((item) => item.index === index);
            if (entry) items.push([entry.count, labels[index]]);
        }
    }
    if (!container.isConnected || !items.length) return;
    container.innerHTML = items
        .map(([value, label]) => `<div><dt>${formatNumber(value)}</dt><dd>${label}</dd></div>`)
        .join("");
    container.hidden = false;
}
