import { api, app, formatNumber } from "./core.js";

const REPO = "https://github.com/haafus/mythoscope";
const AWESOME = "https://github.com/haafus/awesome-computational-mythology";
const PREPRINT = "https://arxiv.org/abs/2610.28452";
const EMAIL = "hello@mythoscope.io";
const TABS = ["vision", "methodology", "contribute", "resources"];

export function renderAbout(params) {
    const initial = TABS.includes(params?.get("tab")) ? params.get("tab") : TABS[0];

    app.innerHTML = `
        <main class="about-page">
            <nav class="nav-menu">
                <button class="nav-item" type="button" data-tab="vision">Vision</button>
                <span class="separator">|</span>
                <button class="nav-item" type="button" data-tab="methodology">Methodology</button>
                <span class="separator">|</span>
                <button class="nav-item" type="button" data-tab="contribute">Contribute</button>
                <span class="separator">|</span>
                <button class="nav-item" type="button" data-tab="resources">Resources</button>
            </nav>

            <div class="content-container">
                <div id="vision" class="tab-content">
                    <p class="about-lead">An open, collaborative infrastructure for the comparative study of mythology, religion and ancient literature, integrating established interpretive methods with artificial intelligence.</p>

                    <h3>Why</h3>
                    <ol class="about-points">
                        <li><strong>Reading has limits.</strong> No scholar can read and compare thousands of texts, and a hand-picked sample can't be redrawn or tested.</li>
                        <li><strong>The indexes and the expertise are fragmented.</strong> Motif indexes are hand-compiled, centred on Europe and Western Asia and detached from the texts; specialists know one tradition deeply, rarely several.</li>
                        <li><strong>Computation opens a new scale, but the work is too big for one team.</strong> NLP and AI make it possible to look for patterns across the whole corpus at once; turning that into findings needs specialists from many fields, so the project is open.</li>
                    </ol>

                    <h3>Status</h3>
                    <p>Early-stage, actively developed research software. The application is live, the <a href="${REPO}" target="_blank" rel="noopener">code is open</a>, and the semantic-space baseline is described in a <a href="${PREPRINT}" target="_blank" rel="noopener">preprint on arXiv</a> (Ganziuk, Humonen, Makarov &amp; Lebedev, 2026). Results so far are exploratory and documented with their data, method and limitations.</p>
                    <p class="about-figures" hidden></p>

                    <h3>What's ahead</h3>
                    <p>A larger and better-balanced corpus, motif induction from the texts themselves, and case studies with specialists in individual traditions.</p>
                </div>

                <div id="methodology" class="tab-content">
                    <h3>Two layers of data</h3>
                    <p><strong>A text corpus.</strong> Primary texts of mythological and religious traditions from open sources, split into fragments and embedded in one semantic space, so that passages can be compared by meaning across traditions. The pipeline is incremental: adding a text rebuilds only what it affects.</p>
                    <p><strong>Three folklore indexes.</strong> Thompson's <em>Motif-Index of Folk-Literature</em> (TMI), the Aarne–Thompson–Uther tale types (ATU) and the Berezkin &amp; Duvakin catalogue, cross-linked into one motif database. Links stated by the indexes themselves are kept apart from inferred ones, which are marked by source and confidence.</p>

                    <h3>Principles</h3>
                    <ul class="about-list">
                        <li>Results are passages with provenance, not generated explanations.</li>
                        <li>Semantic parallels between motifs are hints for expert review, not established links.</li>
                        <li>Uneven collecting is a known bias, carried into the analyses rather than ignored.</li>
                        <li>Negative results are reported too: for example, a motif's first written attestation does not predict its age as estimated from its distribution, so written dates serve only as lower bounds.</li>
                    </ul>

                    <h3>Known limits</h3>
                    <p>Motif induction from raw text is built but not yet validated at scale, so the analyses run on the curated indexes. The indexes keep their compilers' geographic biases, and tradition locations are the catalogue's hand-placed markers.</p>
                </div>

                <div id="contribute" class="tab-content">
                    <p class="about-lead">Open to collaboration with folklorists, specialists in individual traditions, computational linguists, ML engineers and developers.</p>

                    <h3>Ways to help</h3>
                    <ul class="about-list">
                        <li><strong>Texts</strong>: vetted translations and editions, especially from under-represented traditions.</li>
                        <li><strong>Methods</strong>: motif induction from text and its evaluation, the main open problem.</li>
                        <li><strong>Expert review</strong>: corrections to texts, the tradition taxonomy and motif links; reporting what looks wrong already helps.</li>
                        <li><strong>Code</strong>: a Python pipeline with a plain JavaScript interface; see the <a href="${REPO}/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">contributing guide</a>.</li>
                        <li><strong>Case studies</strong> designed and checked together with specialists in individual traditions.</li>
                    </ul>

                    <h3>Credit</h3>
                    <p>Every contribution is credited, from acknowledgement up to co-authorship for substantial work. Material belonging to living communities is handled under the CARE principles, including the right to have it removed.</p>

                    <h3>Get in touch</h3>
                    <p>Open an issue on <a href="${REPO}/issues" target="_blank" rel="noopener">GitHub</a> or write to <a href="mailto:${EMAIL}">${EMAIL}</a>.</p>
                </div>

                <div id="resources" class="tab-content">
                    <h3>For the field</h3>
                    <ul class="about-list">
                        <li><a href="${AWESOME}" target="_blank" rel="noopener"><strong>Awesome Computational Mythology</strong></a>: a curated list of indexes, datasets, methods, tools, papers and venues.</li>
                        <li><a href="${REPO}/tree/main/docs/research" target="_blank" rel="noopener"><strong>Survey of the field</strong></a>: computational work on myth and folklore since 2008, motif induction, dating methods and sources per tradition.</li>
                    </ul>

                    <h3>Data sources and licences</h3>
                    <ul class="about-list">
                        <li><strong>Berezkin &amp; Duvakin</strong> catalogue (<a href="http://areasofmyths.com" target="_blank" rel="noopener">areasofmyths.com</a>), CC BY-NC-SA 4.0.</li>
                        <li><strong>Thompson and ATU</strong> via <a href="https://github.com/j-hagedorn/trilogy" target="_blank" rel="noopener">j-hagedorn/trilogy</a> (CC BY-SA 4.0) and Katja Mellmann's <a href="https://github.com/KatjaMellmann/TMI_as_CSV" target="_blank" rel="noopener">TMI_as_CSV</a> (CC BY 4.0).</li>
                        <li><strong>Texts</strong> from open digital libraries such as Project Gutenberg; each source links to the edition used.</li>
                        <li><strong>Mythoscope</strong>: code MIT, documentation CC BY-SA 4.0, derived datasets CC BY 4.0 (<a href="${REPO}/blob/main/LICENSE" target="_blank" rel="noopener">LICENSE</a>).</li>
                    </ul>

                    <h3>How to cite</h3>
                    <p>Until the first archived release has a DOI, cite the preprint, <a href="${PREPRINT}" target="_blank" rel="noopener">arXiv:2610.28452</a> (BibTeX on its page), and name the software version you used.</p>
                </div>
            </div>

            <footer class="about-contact">
                <div><span class="about-contact-label">Contact</span><a href="mailto:${EMAIL}">${EMAIL}</a></div>
                <div><span class="about-contact-label">Code</span><a href="${REPO}" target="_blank" rel="noopener">github.com/haafus/mythoscope</a></div>
            </footer>
        </main>
    `;

    const show = (tab) => {
        app.querySelectorAll(".tab-content").forEach((content) => content.classList.toggle("active", content.id === tab));
        app.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.tab === tab));
    };
    show(initial);

    app.querySelectorAll(".nav-item").forEach((button) => {
        button.addEventListener("click", () => {
            show(button.dataset.tab);
            // replaceState keeps the tab shareable without firing hashchange (a full re-render).
            history.replaceState(null, "", `#/about?tab=${button.dataset.tab}`);
        });
    });

    renderStats(app.querySelector(".about-figures"));
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
    container.textContent = `Current build: ${items
        .map(([value, label]) => `${formatNumber(value)} ${label}`)
        .join(" · ")}.`;
    container.hidden = false;
}
