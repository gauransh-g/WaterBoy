"""
Unit tests for text chunking logic.
"""

from app.rag.chunker import TextChunker


def test_chunker_basic_split():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = (
        "Groundwater is a vital natural resource across India.\n\n"
        "The Central Ground Water Board conducts periodic assessments.\n\n"
        "Atal Bhujal Yojana promotes community groundwater management."
    )
    chunks = chunker.split_text(
        text=text,
        source_doc="test_doc.md",
        title="Test Document",
        section="Intro"
    )
    
    assert len(chunks) >= 2
    assert chunks[0].metadata["source_doc"] == "test_doc.md"
    assert chunks[0].metadata["title"] == "Test Document"
    assert chunks[0].chunk_id.startswith("test_doc_md_0_")


def test_chunker_metadata_preservation():
    chunker = TextChunker(chunk_size=300, chunk_overlap=50)
    text = "Punjab exhibits severe over-exploitation of alluvial aquifers due to intensive paddy cultivation."
    chunks = chunker.split_text(
        text=text,
        source_doc="punjab.md",
        title="Punjab Assessment",
        state="Punjab",
        district="Ludhiana",
        year="2023-2024"
    )
    
    assert len(chunks) == 1
    assert chunks[0].metadata["state"] == "Punjab"
    assert chunks[0].metadata["district"] == "Ludhiana"
    assert chunks[0].metadata["year"] == "2023-2024"

