import "./_stub-dom.mjs";
import assert from "node:assert/strict";
import { test } from "node:test";

import {
    bookTitleFromId,
    buildCorpusApiUrl,
    corpusTraditionKey,
    escapeHtml,
    escapeRegex,
    formatNumber,
    groupDocuments,
    normalizePreviewText,
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
    assert.equal(corpusTraditionKey("Indo-European", "Greek"), "Indo-European|Greek");
    assert.equal(corpusTraditionKey("", ""), "Other|Unknown");
});

test("bookTitleFromId reverses the id normalization", () => {
    assert.equal(bookTitleFromId("The_Iliad.txt"), "The Iliad");
    assert.equal(bookTitleFromId(""), "");
});

test("buildCorpusApiUrl encodes params and defaults source", () => {
    const url = buildCorpusApiUrl({ title: "A B", major_tradition: "E", tradition: "Greek" });
    assert.equal(url, "/api/corpus/documents?title=A+B&major_tradition=E&tradition=Greek&source=corpus");
});

test("groupDocuments nests by major then tradition, with defaults", () => {
    const grouped = groupDocuments([
        { major_tradition: "European", tradition: "Greek" },
        { major_tradition: "European", tradition: "Norse" },
        {},
    ]);
    assert.equal(grouped.get("European").get("Greek").length, 1);
    assert.equal(grouped.get("European").get("Norse").length, 1);
    assert.equal(grouped.get("Other").get("Unknown").length, 1);
});
