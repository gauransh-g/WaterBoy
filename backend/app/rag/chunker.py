"""
Text chunking and metadata extraction for groundwater documents.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional


class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata
        }


class TextChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(
        self,
        text: str,
        source_doc: str,
        title: str,
        section: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        year: Optional[str] = "2023-2024",
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Split text into overlapping semantic chunks, preserving paragraphs and sentences.
        """
        # Normalize whitespace and line breaks
        cleaned_text = re.sub(r"\r\n", "\n", text).strip()
        paragraphs = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]

        chunks: List[DocumentChunk] = []
        current_chunk_paragraphs = []
        current_length = 0
        chunk_index = 0

        for para in paragraphs:
            para_len = len(para)
            if current_length + para_len > self.chunk_size and current_chunk_paragraphs:
                # Flush current chunk
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                chunk_id = self._generate_chunk_id(source_doc, chunk_index)
                
                meta = {
                    "source_doc": source_doc,
                    "title": title,
                    "section": section or "General",
                    "state": state,
                    "district": district,
                    "year": year,
                    "chunk_index": chunk_index,
                    **(extra_metadata or {})
                }
                chunks.append(DocumentChunk(chunk_id, chunk_text, meta))
                chunk_index += 1

                # Retain overlap from last paragraph if reasonable
                if self.chunk_overlap > 0 and len(current_chunk_paragraphs[-1]) <= self.chunk_overlap * 2:
                    current_chunk_paragraphs = [current_chunk_paragraphs[-1], para]
                    current_length = len(current_chunk_paragraphs[0]) + para_len
                else:
                    current_chunk_paragraphs = [para]
                    current_length = para_len
            else:
                current_chunk_paragraphs.append(para)
                current_length += para_len

        # Remaining paragraphs
        if current_chunk_paragraphs:
            chunk_text = "\n\n".join(current_chunk_paragraphs)
            chunk_id = self._generate_chunk_id(source_doc, chunk_index)
            meta = {
                "source_doc": source_doc,
                "title": title,
                "section": section or "General",
                "state": state,
                "district": district,
                "year": year,
                "chunk_index": chunk_index,
                **(extra_metadata or {})
            }
            chunks.append(DocumentChunk(chunk_id, chunk_text, meta))

        return chunks

    def _generate_chunk_id(self, source_doc: str, index: int) -> str:
        base = f"{source_doc}_{index}"
        hash_suffix = hashlib.md5(base.encode("utf-8")).hexdigest()[:8]
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", source_doc)
        return f"{clean_name}_{index}_{hash_suffix}"

