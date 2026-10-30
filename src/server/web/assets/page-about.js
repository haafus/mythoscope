import { app, onCleanup } from "./core.js";

const REPO = "https://github.com/haafus/mythoscope";
const AWESOME = "https://github.com/haafus/awesome-computational-mythology";
const PREPRINT = "https://arxiv.org/abs/2610.28452";
const EMAIL = "hello@mythoscope.io";
const EXT = 'target="_blank" rel="noopener"';
const SECTIONS = [["vision", "Vision"], ["contribute", "Contribute"], ["resources", "Resources"], ["contact", "Contact"]];

const ICON_MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 6.5 8.5 6.5 8.5-6.5"/></svg>';
const ICON_GITHUB = '<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>';
const ICON_PAPER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/></svg>';

function contactRow(icon, label, href, text, external = true) {
    return `<a class="about-contact" href="${href}" title="${label}"${external ? ` ${EXT}` : ""}>`
        + `<span class="about-contact-icon">${icon}</span><span>${text}</span></a>`;
}

export function renderAbout(params) {
    app.innerHTML = `
        <main class="about-page">
            <div class="about-layout">
                <nav class="about-rail" aria-label="On this page">
                    ${SECTIONS.map(([id, title]) => `<a class="about-rail-group" href="#${id}" data-section="${id}">${title}</a>`).join("")}
                </nav>
                <article class="card about-card">
                <section id="vision">
                    <h2 class="about-group-title">Vision</h2>
                    <p class="about-intro">An open, collaborative infrastructure for the comparative study of mythology, religion and ancient literature, integrating established interpretive methods with artificial intelligence.</p>
                    <h3 class="about-label">Why</h3>
                    <ol class="about-list">
                        <li><strong>Reading has limits.</strong> No scholar can read and compare thousands of texts across traditions, and a hand-picked sample can't be redrawn or tested.</li>
                        <li><strong>The indexes and the expertise are fragmented.</strong> Motif indexes are hand-compiled, centred on Europe and Western Asia and detached from the texts; specialists know one tradition deeply, rarely several.</li>
                        <li><strong>Computation opens a new scale.</strong> NLP and AI make it possible to look for patterns across the whole corpus at once.</li>
                        <li><strong>The work is too big for one team.</strong> Turning those patterns into findings needs specialists from many fields, so the project is open.</li>
                    </ol>
                    <h3 class="about-label">What's done so far</h3>
                    <ul class="about-list">
                        <li><strong>A seed corpus</strong> of primary mythological and religious texts from traditions across the world, drawn from open sources.</li>
                        <li><strong>Basic tools for exploring similarity and structure:</strong> finding parallel passages across traditions by meaning, and mapping characters, places and times within each text.</li>
                        <li><strong>Three major folklore indexes, cross-linked:</strong> Thompson, Aarne–Thompson–Uther and Berezkin &amp; Duvakin, with a graph of how their motifs and tale types relate.</li>
                        <li><strong>A public interface:</strong> this site, open to anyone without installation.</li>
                        <li><strong>A first preprint:</strong> <a href="${PREPRINT}" ${EXT}><em>MythoSemantic: An Interactive System for Discovering Semantic Parallels Across Mythological and Religious Traditions</em></a> (Ganziuk, Humonen, Makarov &amp; Lebedev, 2026), a write-up of the basic pipeline.</li>
                        <li><strong>Exploratory studies</strong> on dating motifs, reconstructing ancestral motif repertoires and how repertoires change across regions, each <a href="${REPO}/tree/main/mockups" ${EXT}>documented with its data</a>, method and limitations.</li>
                    </ul>
                    <h3 class="about-label">What's ahead</h3>
                    <p class="about-text">A larger and better-balanced corpus and motif induction from the texts themselves.</p>
                </section>
                <section id="contribute">
                    <h2 class="about-group-title">Contribute</h2>
                    <p class="about-intro">Open to collaboration with folklorists, specialists in individual traditions, computational linguists, ML engineers and developers.</p>
                    <h3 class="about-label">Ways to help</h3>
                    <ul class="about-list">
                        <li><strong>Texts:</strong> vetted translations and editions, especially from under-represented traditions.</li>
                        <li><strong>Methods:</strong> any method or improvement to an existing one is welcome. We are experimenting and still looking for what works; motif induction from text and its evaluation is the main open problem.</li>
                        <li><strong>Expert review:</strong> corrections to texts, the tradition taxonomy and motif links; reporting what looks wrong already helps.</li>
                        <li><strong>Code:</strong> see the <a href="${REPO}/blob/main/CONTRIBUTING.md" ${EXT}>contributing guide</a>.</li>
                        <li><strong>Your own way:</strong> partnerships, joint projects or simply an idea. If you see how you could take part, <a href="#contact">get in touch</a>.</li>
                    </ul>
                </section>
                <section id="resources">
                    <h2 class="about-group-title">Resources</h2>
                    <h3 class="about-label">For the field</h3>
                    <ul class="about-list">
                        <li><a href="${AWESOME}" ${EXT}><strong>Awesome Computational Mythology:</strong></a> a curated list of indexes, datasets, methods, tools, papers and venues.</li>
                        <li><a href="${REPO}/tree/main/docs/research" ${EXT}><strong>Survey of the field:</strong></a> computational work on myth and folklore, motif induction, dating methods and sources per tradition.</li>
                    </ul>
                    <h3 class="about-label">Data sources and licences</h3>
                    <ul class="about-list">
                        <li><strong>Berezkin &amp; Duvakin</strong> catalogue (<a href="http://areasofmyths.com" ${EXT}>areasofmyths.com</a>), CC BY-NC-SA 4.0.</li>
                        <li><strong>Thompson and ATU</strong> via <a href="https://github.com/j-hagedorn/trilogy" ${EXT}>j-hagedorn/trilogy</a> (CC BY-SA 4.0) and Katja Mellmann's <a href="https://github.com/KatjaMellmann/TMI_as_CSV" ${EXT}>TMI_as_CSV</a> (CC BY 4.0).</li>
                        <li><strong>Texts</strong> from open digital libraries such as Project Gutenberg.</li>
                        <li><strong>Mythoscope:</strong> code MIT, documentation CC BY-SA 4.0, derived datasets CC BY 4.0 (<a href="${REPO}/blob/main/LICENSE" ${EXT}>LICENSE</a>).</li>
                    </ul>
                    <h3 class="about-label">How to cite</h3>
                    <p class="about-text">Cite the preprint, <a href="${PREPRINT}" ${EXT}>arXiv:2610.28452</a> (BibTeX on its page).</p>
                </section>
                <section id="contact">
                    <h2 class="about-group-title">Contact</h2>
                    <div class="about-contacts">
                        ${contactRow(ICON_MAIL, "Email", `mailto:${EMAIL}`, EMAIL, false)}
                        ${contactRow(ICON_GITHUB, "GitHub", REPO, "github.com/haafus/mythoscope")}
                        ${contactRow(ICON_PAPER, "Paper", PREPRINT, "arXiv:2610.28452")}
                    </div>
                </section>
                </article>
            </div>
        </main>
    `;

    const page = app.querySelector(".about-page");
    const sections = SECTIONS.map(([id]) => app.querySelector(`#${id}`));
    const links = [...app.querySelectorAll(".about-rail-group")];
    // Wide screens scroll the page pane; below 980px the whole document scrolls instead.
    const docScrolls = () => getComputedStyle(page).overflowY === "visible";
    const scrollTop = () => (docScrolls() ? window.scrollY : page.scrollTop);
    const topOf = (el) => el.getBoundingClientRect().top + scrollTop()
        - (docScrolls() ? 0 : page.getBoundingClientRect().top);
    // A section picked from the menu stays highlighted while the page scrolls to it,
    // even when the page bottoms out before that section reaches the top.
    let picked = null;
    const scrollToSection = (id, behavior = "smooth") => {
        const target = app.querySelector(`#${id}`);
        if (!target) return;
        picked = id;
        highlight();
        (docScrolls() ? window : page).scrollTo({ top: topOf(target) - 20, behavior });
    };

    // In-page links are handled here: a plain #id would be read by the hash router as a route.
    app.querySelectorAll('.about-page a[href^="#"]').forEach((link) => {
        const id = link.getAttribute("href").slice(1);
        if (!SECTIONS.some(([sectionId]) => sectionId === id)) return;
        link.addEventListener("click", (event) => {
            event.preventDefault();
            scrollToSection(id);
            history.replaceState(null, "", `#/about?section=${id}`);
        });
    });

    function highlight() {
        if (picked) {
            links.forEach((link) => link.classList.toggle("active", link.dataset.section === picked));
            return;
        }
        const top = scrollTop();
        const height = docScrolls() ? window.innerHeight : page.clientHeight;
        const total = docScrolls() ? document.documentElement.scrollHeight : page.scrollHeight;
        let current = 0;
        sections.forEach((section, i) => { if (topOf(section) <= top + 40) current = i; });
        if (top + height >= total - 2) current = sections.length - 1;
        links.forEach((link, i) => link.classList.toggle("active", i === current));
    }
    const release = () => { picked = null; };
    ["wheel", "touchstart", "keydown"].forEach((type) => window.addEventListener(type, release, { passive: true }));
    onCleanup(() => ["wheel", "touchstart", "keydown"].forEach((type) => window.removeEventListener(type, release)));
    page.addEventListener("scroll", highlight, { passive: true });
    window.addEventListener("scroll", highlight, { passive: true });
    onCleanup(() => window.removeEventListener("scroll", highlight));

    // ?tab= is the old name of the parameter; links shared before the one-page layout still land.
    const initial = params?.get("section") || params?.get("tab");
    if (initial) scrollToSection(initial, "auto");
    highlight();
}
