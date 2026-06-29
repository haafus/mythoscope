SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "。", "！", "？", "।", "; ", ", ", "、", " ", ""]


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:

    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    def _extract_tail(chunk: str, overlap_size: int) -> str:
        if overlap_size <= 0 or len(chunk) <= overlap_size:
            return ""
        tail_start = len(chunk) - overlap_size
        for sep in SEPARATORS:
            if not sep:
                continue
            search_start = max(0, tail_start - 50)
            last_sep_pos = chunk.rfind(sep, search_start, len(chunk))
            if last_sep_pos != -1 and last_sep_pos >= tail_start - 100:
                return chunk[last_sep_pos + len(sep) :]
        return chunk[-overlap_size:]

    def _split_recursive(text_to_split: str, seps: list[str], tail: str = "", depth: int = 0) -> list[str]:
        MAX_DEPTH = 10
        if depth > MAX_DEPTH:
            step = chunk_size - chunk_overlap
            if step <= 0:
                step = chunk_size // 2
            return [text_to_split[i : i + chunk_size] for i in range(0, len(text_to_split), step)]

        if not seps:
            full_text = tail + text_to_split
            if len(full_text) <= chunk_size:
                return [full_text]
            chunks = []
            step = chunk_size - chunk_overlap
            if step <= 0:
                step = chunk_size // 2
            for i in range(0, len(full_text), step):
                chunk = full_text[i : i + chunk_size]
                if chunk:
                    chunks.append(chunk)
            return chunks

        separator = seps[0]
        remaining_seps = seps[1:]
        if separator:
            splits = text_to_split.split(separator)
            splits = [s + (separator if i < len(splits) - 1 else "") for i, s in enumerate(splits) if s]
        else:
            splits = [text_to_split] if text_to_split else []

        if tail and splits:
            splits[0] = tail + splits[0]
            tail = ""
        chunks, current_chunk, current_tail = [], "", ""

        for split in splits:
            if len(current_chunk) + len(split) <= chunk_size:
                current_chunk += split
            else:
                if current_chunk:
                    current_tail = _extract_tail(current_chunk, chunk_overlap)
                    chunks.append(current_chunk)
                if len(split) > chunk_size:
                    sub_chunks = _split_recursive(split, remaining_seps, current_tail, depth + 1)
                    if sub_chunks:
                        chunks.extend(sub_chunks)
                        current_chunk = _extract_tail(sub_chunks[-1], chunk_overlap)
                        current_tail = ""
                    else:
                        current_chunk = current_tail
                else:
                    current_chunk = current_tail + split
                    current_tail = ""
        if current_chunk:
            chunks.append(current_chunk)
        return _merge_small_chunks(chunks, chunk_size)

    def _overlap_len(cur: str, nxt: str) -> int:
        """How much of nxt's start duplicates the end of cur (the prepended overlap).

        Capped at chunk_overlap: on repetitive text a longer suffix==prefix match is
        coincidental, not real overlap, so stripping it would delete content (the cap
        means we may leave a little overlap rather than ever over-strip).
        """
        if chunk_overlap <= 0:
            return 0
        cap = min(len(cur), len(nxt), chunk_overlap)
        for k in range(cap, 0, -1):
            if cur[-k:] == nxt[:k]:
                return k
        return 0

    def _merge_small_chunks(chunks: list[str], max_size: int) -> list[str]:
        """Absorb a too-small chunk into its predecessor, staying within max_size.

        The next chunk still begins with the overlap tail of the previous one, so the
        duplicated prefix is stripped before joining — otherwise the merged chunk would
        contain that overlap twice. Merging is skipped when the join would exceed
        max_size (the bound is the chunk budget, not a soft 1.2x of it).
        """
        if not chunks:
            return []
        merged = [chunks[0]]
        for nxt in chunks[1:]:
            cur = merged[-1]
            body = nxt[_overlap_len(cur, nxt):]
            if len(cur) + len(body) <= max_size:
                merged[-1] = cur + body
            else:
                merged.append(nxt)
        return merged

    return _split_recursive(text, SEPARATORS)
