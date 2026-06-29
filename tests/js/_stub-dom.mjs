// Minimal browser globals so the asset modules import under `node --test`.
// core.js reads document/localStorage at module load; nothing tested here uses
// them at call time, so empty stubs are enough.
globalThis.document = { getElementById: () => null };
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
