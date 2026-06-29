import "./_stub-dom.mjs";
import assert from "node:assert/strict";
import { test } from "node:test";

import {
    attributionLine,
    chunkMetaLine,
    highlightText,
    resultBookTitle,
    scoreClass,
    searchResultMetaLine,
} from "../../src/server/web/assets/search-utils.js";

test("scoreClass buckets percent into score tiers", () => {
    assert.deepEqual(scoreClass(0.7), { percent: 70, cls: "score-high" });
    assert.deepEqual(scoreClass(0.5), { percent: 50, cls: "score-medium" });
    assert.deepEqual(scoreClass(0.2), { percent: 20, cls: "score-low" });
    assert.deepEqual(scoreClass(null), { percent: 0, cls: "score-low" });
});

test("resultBookTitle prefers filename, then id, then a fallback", () => {
    assert.equal(resultBookTitle({ filename: "My_Book.txt" }), "My Book");
    assert.equal(resultBookTitle({ id: "X_Y" }), "X Y");
    assert.equal(resultBookTitle({}), "Unknown book");
});

test("chunkMetaLine / searchResultMetaLine compose the expected text", () => {
    const item = { filename: "A_B.txt", chunk_index: 3, tradition: "Greek" };
    assert.equal(chunkMetaLine(item), "Book: A B | Chunk #3");
    assert.equal(searchResultMetaLine(item), "Tradition: Greek | Book: A B | Chunk #3");
    assert.equal(chunkMetaLine({}), "Book: Unknown book | Chunk #0");
});

test("attributionLine escapes fields and appends score only when asked", () => {
    const html = attributionLine({ tradition: "<b>", chunk_index: 1, similarity_score: 0.756 }, { withScore: true });
    assert.ok(html.includes("&lt;b&gt;"));
    assert.ok(html.includes("score 0.76"));
    const plain = attributionLine({ tradition: "Greek", chunk_index: 1, similarity_score: 0.756 });
    assert.ok(!plain.includes("score"));
});

test("highlightText wraps long query words and escapes the rest", () => {
    assert.equal(highlightText("the cat sat", "cat"), "the <mark>cat</mark> sat");
    assert.equal(highlightText("<x>", "cat"), "&lt;x&gt;");  // no match -> just escaped
    assert.equal(highlightText("a b", ""), "a b");           // empty query -> escaped passthrough
});
