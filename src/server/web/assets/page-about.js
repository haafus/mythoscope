import { app } from "./core.js";

const REPO = "https://github.com/haafus/mythoscope";
const AWESOME = "https://github.com/haafus/awesome-computational-mythology";
const PREPRINT = "https://arxiv.org/abs/2610.28452";
const EMAIL = "hello@mythoscope.io";
const TABS = ["vision", "contribute", "resources"];

export function renderAbout(params) {
    const initial = TABS.includes(params?.get("tab")) ? params.get("tab") : TABS[0];

    app.innerHTML = `
        <main class="about-page">
            <nav class="nav-menu">
                <button class="nav-item" type="button" data-tab="vision">Vision</button>
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

                    <h3>What's done so far</h3>
                    <ul class="about-list">
                        <li><strong>A published baseline</strong>: the semantic-space approach and its lexical controls are described in a <a href="${PREPRINT}" target="_blank" rel="noopener">preprint on arXiv</a> (Ganziuk, Humonen, Makarov &amp; Lebedev, 2026).</li>
                        <li><strong>Exploratory studies</strong> on dating motifs, reconstructing ancestral motif repertoires and how repertoires change across regions, each <a href="${REPO}/tree/main/mockups" target="_blank" rel="noopener">documented</a> with its data, method and limitations.</li>
                    </ul>

                    <h3>What's ahead</h3>
                    <p>A larger and better-balanced corpus and motif induction from the texts themselves.</p>
                </div>

                <div id="contribute" class="tab-content">
                    <p class="about-lead">Open to collaboration with folklorists, specialists in individual traditions, computational linguists, ML engineers and developers.</p>

                    <h3>Ways to help</h3>
                    <ul class="about-list">
                        <li><strong>Texts</strong>: vetted translations and editions, especially from under-represented traditions.</li>
                        <li><strong>Methods</strong>: motif induction from text and its evaluation, the main open problem.</li>
                        <li><strong>Expert review</strong>: corrections to texts, the tradition taxonomy and motif links; reporting what looks wrong already helps.</li>
                        <li><strong>Code</strong>: see the <a href="${REPO}/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">contributing guide</a>.</li>
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
                        <li><strong>Texts</strong> from open digital libraries such as Project Gutenberg.</li>
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
}
