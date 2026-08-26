"""Parsers for NLM/PubMed .nbib and RIS bibliography files."""

import re
from pathlib import Path

import pandas as pd

# Tags that can legitimately repeat within a single record and should be
# collected into a list rather than overwritten.
NBIB_REPEATABLE_TAGS = {
    "AU", "AUID", "AD", "FAU", "IR", "IRAD", "FIR",
    "MH", "OT", "OTO", "PT", "SI", "GR", "GN", "CIN", "CON",
    "EIN", "ERI", "CI", "LA", "PL", "GS", "ID",
}

# RIS tags that can legitimately repeat within a single record.
RIS_REPEATABLE_TAGS = {"AU", "A2", "A3", "A4", "KW", "N1", "UR", "L1", "L2"}

TAG_LINE_RE = re.compile(r"^([A-Za-z]{2,4})\s*-\s?(.*)$")
RIS_TAG_LINE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]{1})\s{2}-\s?(.*)$")


def _load_text(source):
    """Return raw text for a source that may be a file path or literal text."""
    path = Path(source)
    try:
        if path.exists():
            return path.read_text(encoding="utf-8-sig")
    except OSError:
        pass
    return source


class BibParser:
    """Parses NLM/PubMed .nbib files into dictionaries or a pandas DataFrame."""

    def parse(self, source):
        """Parse an .nbib file path or raw .nbib text into a list of record dicts.

        Args:
            source: path to an .nbib file, or a string containing .nbib text.

        Returns:
            list[dict]: one dict per record, keyed by NLM tag (e.g. "PMID", "TI", "AU").
                Repeatable tags (e.g. "AU", "MH") are returned as lists of strings.
        """
        text = _load_text(source)
        return self._parse_records(text)

    def parse_to_dataframe(self, source):
        """Parse an .nbib file path or raw .nbib text into a pandas DataFrame.

        Args:
            source: path to an .nbib file, or a string containing .nbib text.

        Returns:
            pd.DataFrame: one row per record. Repeatable-tag columns hold lists.
        """
        records = self.parse(source)
        return pd.DataFrame(records)

    def _parse_records(self, text):
        records = []
        current = {}
        last_tag = None

        for raw_line in text.splitlines():
            if not raw_line.strip():
                if current:
                    records.append(current)
                    current = {}
                    last_tag = None
                continue

            match = TAG_LINE_RE.match(raw_line)
            if match:
                tag, value = match.group(1), match.group(2).strip()
                last_tag = tag
                if tag in NBIB_REPEATABLE_TAGS:
                    current.setdefault(tag, []).append(value)
                else:
                    current[tag] = value
            elif last_tag is not None:
                # Continuation line: append to the most recent tag's value.
                continuation = raw_line.strip()
                if last_tag in NBIB_REPEATABLE_TAGS:
                    current[last_tag][-1] = f"{current[last_tag][-1]} {continuation}".strip()
                else:
                    current[last_tag] = f"{current.get(last_tag, '')} {continuation}".strip()

        if current:
            records.append(current)

        return records


class RisParser:
    """Parses RIS (.ris) files into dictionaries or a pandas DataFrame."""

    def parse(self, source):
        """Parse a .ris file path or raw RIS text into a list of record dicts.

        Args:
            source: path to a .ris file, or a string containing RIS text.

        Returns:
            list[dict]: one dict per record, keyed by RIS tag (e.g. "TY", "TI", "AU").
                Repeatable tags (e.g. "AU", "KW") are returned as lists of strings.
        """
        text = _load_text(source)
        return self._parse_records(text)

    def parse_to_dataframe(self, source):
        """Parse a .ris file path or raw RIS text into a pandas DataFrame.

        Args:
            source: path to a .ris file, or a string containing RIS text.

        Returns:
            pd.DataFrame: one row per record. Repeatable-tag columns hold lists.
        """
        records = self.parse(source)
        return pd.DataFrame(records)

    def _parse_records(self, text):
        records = []
        current = {}
        last_tag = None

        for raw_line in text.splitlines():
            if not raw_line.strip():
                continue

            match = RIS_TAG_LINE_RE.match(raw_line)
            if match:
                tag, value = match.group(1), match.group(2).strip()
                if tag == "ER":
                    if current:
                        records.append(current)
                    current = {}
                    last_tag = None
                    continue

                last_tag = tag
                if tag in RIS_REPEATABLE_TAGS:
                    current.setdefault(tag, []).append(value)
                else:
                    current[tag] = value
            elif last_tag is not None:
                # Continuation line: append to the most recent tag's value.
                continuation = raw_line.strip()
                if last_tag in RIS_REPEATABLE_TAGS:
                    current[last_tag][-1] = f"{current[last_tag][-1]} {continuation}".strip()
                else:
                    current[last_tag] = f"{current.get(last_tag, '')} {continuation}".strip()

        if current:
            records.append(current)

        return records
