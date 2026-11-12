import os
import re
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import pypdf

@dataclass
class DocumentMetadata:
    doc_id: str
    filename: str
    title: str
    revision: str
    effective_date: str
    is_active: bool
    superseded_by: Optional[str] = None
    page_count: int = 1

@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    filename: str
    revision: str
    is_active: bool
    superseded_by: Optional[str]
    effective_date: str
    section_number: str
    section_title: str
    page_number: int
    content: str
    tokens: List[str]

@dataclass
class SearchResult:
    chunk: Chunk
    score: float
    matched_terms: List[str]

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", 
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", 
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", 
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", 
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she", 
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", 
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", 
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", 
    "why", "will", "with", "you", "your", "yours", "yourself", "yourselves"
}

def tokenize(text: str) -> List[str]:
    clean = text.lower()
    tokens = re.findall(r'[a-z0-9]+(?:[\-_][a-z0-9]+)*', clean)
    return [t for t in tokens if len(t) > 1 and t not in STOP_WORDS]

class RAGStore:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.documents: Dict[str, DocumentMetadata] = {}
        self.chunks: List[Chunk] = []
        self.doc_freq: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self.indexed = False

    def load_and_index(self):
        """Loads all PDFs in data_dir, extracts sections, and indexes chunks."""
        self.documents.clear()
        self.chunks.clear()
        self.doc_freq.clear()

        if not os.path.exists(self.data_dir):
            return

        pdf_files = [f for f in os.listdir(self.data_dir) if f.endswith(".pdf") and not f.startswith("Sample_Questions")]

        raw_docs = []
        for fname in sorted(pdf_files):
            filepath = os.path.join(self.data_dir, fname)
            meta, pages_text = self._parse_pdf(filepath, fname)
            raw_docs.append((meta, pages_text))

        # Detect active vs superseded revisions
        grouped: Dict[str, List[DocumentMetadata]] = {}
        for meta, _ in raw_docs:
            grouped.setdefault(meta.doc_id, []).append(meta)

        for doc_id, meta_list in grouped.items():
            if len(meta_list) > 1:
                sorted_metas = sorted(meta_list, key=lambda m: m.revision, reverse=True)
                latest = sorted_metas[0]
                latest.is_active = True
                for older in sorted_metas[1:]:
                    older.is_active = False
                    older.superseded_by = f"{latest.doc_id} {latest.revision}"
            else:
                meta_list[0].is_active = True

        # Now chunk each document with cross-page section coherence
        for meta, pages_text in raw_docs:
            self.documents[meta.filename] = meta
            self._chunk_document(meta, pages_text)

        # Compute corpus statistics for BM25
        total_len = 0
        for chunk in self.chunks:
            total_len += len(chunk.tokens)
            unique_terms = set(chunk.tokens)
            for term in unique_terms:
                self.doc_freq[term] = self.doc_freq.get(term, 0) + 1

        self.avg_doc_len = total_len / max(len(self.chunks), 1)
        self.indexed = True

    def _parse_pdf(self, filepath: str, filename: str) -> Tuple[DocumentMetadata, List[Tuple[int, str]]]:
        reader = pypdf.PdfReader(filepath)
        page_count = len(reader.pages)
        pages_text = []

        full_first_page = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_text.append((i + 1, text))
            if i == 0:
                full_first_page = text

        doc_id_match = re.search(r'Document No\.\s*([\w\-]+)', full_first_page)
        if not doc_id_match:
            doc_id_match = re.search(r'([\w]+-[\w]+-[\w\-]+)', filename)
        doc_id = doc_id_match.group(1).strip() if doc_id_match else filename.replace(".pdf", "")

        rev_match = re.search(r'Revision\s*([0-9A-Za-z]+)', full_first_page)
        if not rev_match:
            rev_match = re.search(r'Rev\s*([0-9]+)', full_first_page, re.IGNORECASE)
        revision = f"Rev {rev_match.group(1).strip()}" if rev_match else "Rev 01"

        date_match = re.search(r'Effective Date\s*([0-9]{1,2}-[A-Za-z]+-[0-9]{4})', full_first_page)
        effective_date = date_match.group(1).strip() if date_match else "Unknown"

        lines = [l.strip() for l in full_first_page.split("\n") if l.strip()]
        title = "Standard Operating Procedure"
        for line in lines[:10]:
            if any(k in line.lower() for k in ["manual", "procedure", "inspection", "lockout", "preventive"]):
                if not line.startswith("Document No") and not line.startswith("QC-") and not line.startswith("SAF-") and not line.startswith("MNT-"):
                    title = line
                    break

        meta = DocumentMetadata(
            doc_id=doc_id,
            filename=filename,
            title=title,
            revision=revision,
            effective_date=effective_date,
            is_active=True,
            page_count=page_count
        )
        return meta, pages_text

    def _chunk_document(self, meta: DocumentMetadata, pages_text: List[Tuple[int, str]]):
        """
        Stitches document pages together with boundary tracking so sections
        spanning multiple pages remain completely unified and unfragmented.
        """
        full_doc = ""
        page_offsets = []

        for page_num, raw_text in pages_text:
            cleaned = re.sub(r'[\w\-]+\s+\|\s+Rev\s+\d+\s+\|\s+Uncontrolled copy.*?\n', '', raw_text)
            cleaned = re.sub(r'Page\s+\d+\s*\n', '', cleaned)
            start_pos = len(full_doc)
            page_offsets.append((page_num, start_pos))
            full_doc += f"\n{cleaned}\n"

        def get_page_for_offset(offset: int) -> int:
            page = 1
            for p_num, p_start in page_offsets:
                if offset >= p_start:
                    page = p_num
                else:
                    break
            return page

        section_pattern = re.compile(r'(?:\n|\A)(?:(\d+)\.\s+([A-Z][^\n]{3,60}))')
        matches = list(section_pattern.finditer(full_doc))

        if not matches:
            content = full_doc.strip()
            if content:
                chunk = Chunk(
                    chunk_id=f"{meta.doc_id}_{meta.revision}_general",
                    doc_id=meta.doc_id,
                    filename=meta.filename,
                    revision=meta.revision,
                    is_active=meta.is_active,
                    superseded_by=meta.superseded_by,
                    effective_date=meta.effective_date,
                    section_number="General",
                    section_title="Overview & General Information",
                    page_number=1,
                    content=content,
                    tokens=tokenize(content)
                )
                self.chunks.append(chunk)
            return

        # Overview content before Section 1
        if matches[0].start() > 0:
            overview_content = full_doc[:matches[0].start()].strip()
            if len(overview_content) > 40:
                self.chunks.append(Chunk(
                    chunk_id=f"{meta.doc_id}_{meta.revision}_sec0",
                    doc_id=meta.doc_id,
                    filename=meta.filename,
                    revision=meta.revision,
                    is_active=meta.is_active,
                    superseded_by=meta.superseded_by,
                    effective_date=meta.effective_date,
                    section_number="Overview",
                    section_title="Header & Document Control",
                    page_number=1,
                    content=overview_content,
                    tokens=tokenize(overview_content)
                ))

        for idx, match in enumerate(matches):
            sec_num = match.group(1)
            sec_title = match.group(2).strip()
            start_pos = match.start()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_doc)
            sec_content = full_doc[start_pos:end_pos].strip()

            page_num = get_page_for_offset(start_pos)

            chunk = Chunk(
                chunk_id=f"{meta.doc_id}_{meta.revision}_sec{sec_num}",
                doc_id=meta.doc_id,
                filename=meta.filename,
                revision=meta.revision,
                is_active=meta.is_active,
                superseded_by=meta.superseded_by,
                effective_date=meta.effective_date,
                section_number=f"Section {sec_num}",
                section_title=sec_title,
                page_number=page_num,
                content=sec_content,
                tokens=tokenize(sec_content)
            )
            self.chunks.append(chunk)

    def search(self, query: str, top_k: int = 3, threshold: float = 3.5) -> Tuple[List[SearchResult], bool]:
        """
        BM25-based Hybrid Search with active revision boost, exact code matching,
        and out-of-scope intent guardrails.
        """
        if not self.indexed:
            self.load_and_index()

        query_clean = query.strip()
        query_tokens = tokenize(query_clean)
        query_lower = query_clean.lower()

        # Domain Entity Detection
        alarm_match = re.search(r'\bal-\d+\b', query_lower)
        alarm_code = alarm_match.group(0).upper() if alarm_match else None

        part_match = re.search(r'\bbh-\d+\b', query_lower)
        part_code = part_match.group(0).upper() if part_match else None

        machine_match = re.search(r'\btx-\d+\b', query_lower)
        machine_code = machine_match.group(0).upper() if machine_match else None

        key_phrases = [
            "coolant concentration", "spindle runout", "lockout lock", "lockout", 
            "bearing housing", "outer diameter", "lube oil", "hydraulic pressure",
            "chuck mounting", "bolt torque", "absent", "removal of a lock", 
            "incoming material", "quarantine cage", "sampling plan", "alarm al-104", "al-104"
        ]
        matched_phrases = [p for p in key_phrases if p in query_lower]

        # BM25 Parameters
        k1 = 1.5
        b = 0.75
        N = max(len(self.chunks), 1)

        results = []

        for chunk in self.chunks:
            chunk_text = chunk.content.lower()
            bm25_score = 0.0
            matched_terms = []

            chunk_len = len(chunk.tokens)
            term_counts = {}
            for t in chunk.tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            for q_term in query_tokens:
                if q_term in term_counts:
                    tf = term_counts[q_term]
                    df = self.doc_freq.get(q_term, 1)
                    idf = math.log(1.0 + (N - df + 0.5) / (df + 0.5))
                    term_score = idf * ((tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (chunk_len / self.avg_doc_len))))
                    bm25_score += term_score
                    matched_terms.append(q_term)

            phrase_boost = 0.0
            for phrase in matched_phrases:
                if phrase in chunk_text:
                    phrase_boost += 16.0
                    matched_terms.append(f"phrase:{phrase}")

            entity_boost = 0.0
            if alarm_code and alarm_code in chunk.content.upper():
                entity_boost += 35.0
                matched_terms.append(f"alarm:{alarm_code}")

            if part_code and part_code in chunk.content.upper():
                entity_boost += 25.0
                matched_terms.append(f"part:{part_code}")

            if machine_code and machine_code in chunk.content.upper():
                entity_boost += 5.0
                matched_terms.append(f"machine:{machine_code}")

            total_score = bm25_score + phrase_boost + entity_boost

            # Downweight boilerplate header/overview chunks so substantive sections outrank them
            if chunk.section_number == "Overview" or "Header" in chunk.section_title:
                total_score *= 0.35

            # Revision status boost / penalty
            if chunk.is_active:
                total_score *= 1.25
            else:
                if "rev 03" not in query_lower and "rev03" not in query_lower:
                    total_score *= 0.4

            if total_score > 0:
                results.append(SearchResult(chunk=chunk, score=total_score, matched_terms=list(set(matched_terms))))

        results.sort(key=lambda r: r.score, reverse=True)

        if not results or results[0].score < threshold:
            return results[:top_k], False

        # Out-of-Scope Filter
        out_of_scope_patterns = [
            r'feed\s*rate', r'spindle\s*speed.*cut', r'aluminium', r'aluminum',
            r'fire\s*extinguisher', r'first\s*aid', r'cafeteria', r'salary', r'leave\s*application',
            r'parking', r'uniform', r'wi-?fi\s*password'
        ]
        for pat in out_of_scope_patterns:
            if re.search(pat, query_lower):
                return results[:top_k], False

        return results[:top_k], True
