import "./_stub-dom.mjs";
import assert from "node:assert/strict";
import { test } from "node:test";

import {
    buildCorpusApiUrl,
    corpusTraditionKey,
    escapeHtml,
    escapeRegex,
    formatNumber,
    groupDocuments,
    normalizePreviewText,
    regionOf,
    state,
} from "../../src/server/web/assets/core.js";

test("escapeHtml neutralizes all five HTML metacharacters", () => {
    assert.equal(escapeHtml(`<a>&"'`), "&lt;a&gt;&amp;&quot;&#39;");
});

test("escapeHtml coerces null/undefined to empty string", () => {
    assert.equal(escapeHtml(null), "");
    assert.equal(escapeHtml(undefined), "");
});

test("escapeRegex escapes regex metacharacters", () => {
    assert.equal(escapeRegex("a.b*c+"), "a\\.b\\*c\\+");
});

test("normalizePreviewText collapses whitespace and trims", () => {
    assert.equal(normalizePreviewText("  a\n\n b\t c "), "a b c");
});

test("formatNumber groups thousands and falls back to 0", () => {
    assert.equal(formatNumber(1234567), "1,234,567");
    assert.equal(formatNumber(null), "0");
    assert.equal(formatNumber("abc"), "0");
});

test("corpusTraditionKey supplies Other/Unknown defaults", () => {
    assert.equal(corpusTraditionKey("Europe", "Greek"), "Europe|Greek");
    assert.equal(corpusTraditionKey("", ""), "Other|Unknown");
});

test("buildCorpusApiUrl addresses a document by document_id", () => {
    assert.equal(buildCorpusApiUrl({ document_id: "abc123", title: "A B" }),
        "/api/corpus/document?id=abc123");
    assert.equal(buildCorpusApiUrl({}), "/api/corpus/document?id=");
});

test("groupDocuments buckets by region via the tree, in tree order", () => {
    // groupDocuments reads state.traditionTree for structure + order.
    state.traditionTree = {
        Europe: { color: "#4F7A4E", traditions: { Greek: {}, Norse: {} } },
        "East Asia": { color: "#C0392B", traditions: { Chinese: {} } },
    };
    state.treeIndex = new Map([
        ["Greek", { region: "Europe" }], ["Norse", { region: "Europe" }],
        ["Chinese", { region: "East Asia" }],
    ]);
    const grouped = groupDocuments([
        { tradition: "Greek", title: "Iliad" },
        { tradition: "Norse", title: "Edda" },
        { tradition: "Chinese", title: "Journey" },
    ]);
    assert.deepEqual([...grouped.keys()], ["Europe", "East Asia"]);  // tree order
    assert.equal(grouped.get("Europe").get("Greek").length, 1);
    assert.equal(grouped.get("East Asia").get("Chinese").length, 1);
    assert.equal(regionOf("Greek"), "Europe");
});
