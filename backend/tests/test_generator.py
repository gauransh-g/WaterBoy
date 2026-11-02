"""
Unit tests for answer generation and evidence attribution.
"""

from app.rag.chunker import DocumentChunk
from app.rag.generator import GroundedGenerator


def test_generator_sufficient_evidence():
    gen = GroundedGenerator()
    chunk = DocumentChunk(
        chunk_id="chunk_1",
        text="The GEC-2015 formula defines Stage of Extraction as (Total Draft / Extractable Resource) * 100.",
        metadata={
            "source_doc": "methodology.md",
            "title": "CGWB GEC-2015",
            "section": "Formulas"
        }
    )
    
    retrieved = [(chunk, 0.85)]
    answer, citations, confidence, has_evidence, model = gen.generate(
        query="What is the GEC-2015 formula?",
        retrieved_chunks=retrieved,
        min_threshold=0.35
    )
    
    assert has_evidence is True
    assert confidence > 0.7
    assert len(citations) == 1
    assert citations[0].chunk_id == "chunk_1"
    assert "[1]" in answer


def test_generator_insufficient_evidence_refusal():
    gen = GroundedGenerator()
    chunk = DocumentChunk(
        chunk_id="chunk_unrelated",
        text="Random unrelated text.",
        metadata={"source_doc": "unknown.md"}
    )
    
    # Below similarity threshold
    retrieved = [(chunk, 0.15)]
    answer, citations, confidence, has_evidence, model = gen.generate(
        query="What is the stock price of Tesla?",
        retrieved_chunks=retrieved,
        min_threshold=0.35
    )
    
    assert has_evidence is False
    assert confidence == 0.0
    assert len(citations) == 0
    assert "does not contain sufficient documented evidence" in answer

