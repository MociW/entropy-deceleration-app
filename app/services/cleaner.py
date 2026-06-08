import re


def clean_title(title: str) -> str:
    title = re.sub(r"tahun anggaran\s*\d{4}", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+[A-Z]$", "", title.strip())

    prefix_patterns = [
        r"^(?:PENETAPAN\s+)?(?:PERPANJANGAN\s+(?:PERIODE\s+)?)?PELAKSANAAN\s+HIBAH\s+PENELITIAN\s+"
        r"FAKULTAS\s+TEKNIK\s+UNIVERSITAS\s+GADJAH\s+MADA\s+TAHUN\s+\d{4}\s*[-–—\u2013\u2014\"\"]*\s*",

        r"^(?:PERPANJANGAN|PERUBAHAN)?\s*PENETAPAN\s+TIM\s+PROGRAM\s+(?:HIBAH\s+)?PENELITIAN\s+"
        r"(?:DARI\s+ANGGARAN\s+TAHUNAN\s+)?FAKULTAS\s+TEKNIK\s+UNIVERSITAS\s+GADJAH\s+MADA\s+"
        r"TAHUN\s+\d{4}\s*[-–—\u2013\u2014\"\"]*\s*",

        r"^(?:PERPANJANGAN|PERUBAHAN)\s+PENETAPAN\s+TIM\s+PROGRAM\s+(?:HIBAH\s+)?PENELITIAN\s+",

        r"^\[(?:FT|RTA)\s+UGM\][:\s]*",
    ]
    for pat in prefix_patterns:
        title = re.sub(pat, "", title, flags=re.IGNORECASE).strip()

    title = re.sub(
        r"\s*[-â€\"\"S]+\s*(?:DEPARTEMEN|DEPARTEMENT|BAGIAN)\s+[A-Z\s]+"
        r"(?:FAKULTAS\s+TEKNIK\s+UNIVERSITAS\s+GADJAH\s+MADA\s+TAHUN\s+\d{4})?\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()

    return title.strip()


def sanitize_casing(text: str) -> str:
    """
    If the text is fully uppercase, converts it to capitalized/sentence case or title case.
    If it's mixed case, returns it unchanged.
    """
    if not text or not isinstance(text, str):
        return text

    trimmed = text.strip()
    if not trimmed:
        return trimmed

    # Check if the text is fully uppercase (ignoring numbers/symbols)
    letters = [c for c in trimmed if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        words = trimmed.split()
        if len(words) < 25:
            # For short text/titles, convert to Title Case
            title_cased = trimmed.title()
            # Lowercase common prepositions and conjunctions
            lowercase_words = {
                "di", "pada", "dan", "ke", "dari", "dengan", "yang", "oleh", "untuk", "dalam", "atau",
                "in", "of", "and", "the", "to", "for", "with", "on", "at", "by", "an", "a", "as", "or", "but"
            }
            res_words = []
            for idx, w in enumerate(title_cased.split()):
                if w.lower() in lowercase_words and idx > 0:
                    res_words.append(w.lower())
                else:
                    res_words.append(w)
            return " ".join(res_words)
        else:
            # For long text/abstracts, convert to sentence case
            import re
            lowered = trimmed.lower()
            sentences = re.split(r'(\s*[\.\!\?]+\s*)', lowered)
            capitalized_parts = []
            capitalize_next = True
            for part in sentences:
                if not part:
                    continue
                if re.match(r'^\s*[\.\!\?]+\s*$', part):
                    capitalized_parts.append(part)
                    capitalize_next = True
                else:
                    if capitalize_next:
                        match = re.search(r'[a-zA-Z]', part)
                        if match:
                            idx = match.start()
                            part = part[:idx] + part[idx].upper() + part[idx+1:]
                        capitalize_next = False
                    capitalized_parts.append(part)
            return "".join(capitalized_parts)

    return trimmed

