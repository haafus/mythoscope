import "./_stub-dom.mjs";
import assert from "node:assert/strict";
import { test } from "node:test";

import { state } from "../../src/server/web/assets/core.js";
import {
    attributionLine,
    chunkMetaLine,
    highlightText,
    pointTooltipHtml,
    resultBookTitle,
    scoreClass,
    searchResultMetaLine,
} from "../../src/server/web/assets/search-utils.js";

// Hits carry only document_id (B1); title + tradition resolve from the docIndex.
state.docIndex = new Map([
    ["d1", { document_id: "d1", title: "A B", tradition: "Greek" }],
]);

test("scoreClass buckets percent into score tiers", () => {
    assert.deepEqual(scoreClass(0.7), { percent: 70, cls: "score-high" });
    assert.deepEqual(scoreClass(0.5), { percent: 50, cls: "score-medium" });
    assert.deepEqual(scoreClass(0.2), { percent: 20, cls: "score-low" });
    assert.deepEqual(scoreClass(null), { percent: 0, cls: "score-low" });
});

test("resultBookTitle resolves the title from the document reference", () => {
    assert.equal(resultBookTitle({ document_id: "d1" }), "A B");
    assert.equal(resultBookTitle({ document_id: "missing" }), "Unknown book");
    assert.equal(resultBookTitle({}), "Unknown book");
});

test("chunkMetaLine / searchResultMetaLine compose from the resolved reference", () => {
    const item = { document_id: "d1", chunk_index: 3 };
    assert.equal(chunkMetaLine(item), "Book: A B | Chunk #3");
    assert.equal(searchResultMetaLine(item), "Tradition: Greek | Book: A B | Chunk #3");
    assert.equal(chunkMetaLine({}), "Book: Unknown book | Chunk #0");
});

test("attributionLine resolves tradition from the reference and appends score only when asked", () => {
    const html = attributionLine({ document_id: "d1", chunk_index: 1, similarity_score: 0.756 }, { withScore: true });
    assert.ok(html.includes("Greek"));
    assert.ok(html.includes("score 0.76"));
    const plain = attributionLine({ document_id: "d1", chunk_index: 1, similarity_score: 0.756 });
    assert.ok(!plain.includes("score"));
});

test("pointTooltipHtml resolves the scatter point via document_id", () => {
    // The chart.js scatter tooltip must key its object `document_id` (not `id`): the
    // resolver reads item.document_id, so a legacy `{ id }` object left every point
    // unresolved ("unknown book / UNASSIGNED"). Lock the contract both ways.
    const resolved = pointTooltipHtml({ document_id: "d1", chunk_index: 0, text: "hi" });
    assert.ok(resolved.includes("Greek") && resolved.includes("A B"));

    const wrongKey = pointTooltipHtml({ id: "d1", chunk_index: 0, text: "hi" });
    assert.ok(wrongKey.includes("Unknown book") && wrongKey.includes("UNASSIGNED"));
});

test("highlightText wraps long query words and escapes the rest", () => {
    assert.equal(highlightText("the cat sat", "cat"), "the <mark>cat</mark> sat");
    assert.equal(highlightText("<x>", "cat"), "&lt;x&gt;");  // no match -> just escaped
    assert.equal(highlightText("a b", ""), "a b");           // empty query -> escaped passthrough
});
