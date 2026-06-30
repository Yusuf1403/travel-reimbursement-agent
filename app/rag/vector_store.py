"""
FAISS-backed vector store for travel policy documents.

Responsibilities:
1. Load Markdown policy files from ``data/policies/``.
2. Split them into semantically meaningful chunks.
3. Generate embeddings via the configured provider.
4. Persist the FAISS index to disk for fast startup.
5. Retrieve the top-K most relevant chunks for a query.
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import get_settings
from app.exceptions import PolicyNotFoundError, RAGIndexError
from app.rag.embeddings import get_embedding_model

logger = logging.getLogger("app.rag")


class PolicyVectorStore:
    """Manages the FAISS index lifecycle — build, persist, load, query."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._embeddings = get_embedding_model()
        self._store: FAISS | None = None

    # ----- Public API ------------------------------------------------------

    def build_index(self, policy_dir: Path | None = None) -> int:
        """
        Read all ``*.md`` files from *policy_dir*, chunk, embed, and persist.

        Returns the number of chunks indexed.
        """
        policy_dir = policy_dir or self._settings.policies_path
        docs = self._load_documents(policy_dir)
        if not docs:
            raise PolicyNotFoundError(f"No .md files found in {policy_dir}")

        chunks = self._split(docs)
        logger.info("Indexing %d chunks from %d documents", len(chunks), len(docs))

        self._store = FAISS.from_documents(chunks, self._embeddings)
        self._persist()
        return len(chunks)

    def load_index(self) -> None:
        """Load a previously persisted FAISS index from disk."""
        idx_path = self._settings.faiss_index_path
        if not idx_path.exists():
            raise RAGIndexError(f"FAISS index not found at {idx_path}. Run `python scripts/build_index.py` first.")
        self._store = FAISS.load_local(
            str(idx_path),
            self._embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info("FAISS index loaded from %s", idx_path)

    def query(self, question: str, top_k: int | None = None) -> list[Document]:
        """Return the *top_k* most relevant policy chunks."""
        if self._store is None:
            self.load_index()
        k = top_k or self._settings.rag_top_k
        results = self._store.similarity_search(question, k=k)  # type: ignore[union-attr]
        logger.info("RAG query returned %d chunks for: %s", len(results), question[:80])
        return results

    def add_documents(self, docs: list[Document]) -> int:
        """Add new documents to an existing index and re-persist."""
        if self._store is None:
            self.load_index()
        chunks = self._split(docs)
        self._store.add_documents(chunks)  # type: ignore[union-attr]
        self._persist()
        return len(chunks)

    # ----- Internals -------------------------------------------------------

    def _load_documents(self, policy_dir: Path) -> list[Document]:
        """Read every ``.md`` file under *policy_dir* as a LangChain Document."""
        documents: list[Document] = []
        for md_file in sorted(policy_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": md_file.name, "path": str(md_file)},
                )
            )
            logger.debug("Loaded policy: %s (%d chars)", md_file.name, len(text))
        return documents

    def _split(self, docs: list[Document]) -> list[Document]:
        """Chunk documents with recursive character splitting."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._settings.rag_chunk_size,
            chunk_overlap=self._settings.rag_chunk_overlap,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_documents(docs)

    def _persist(self) -> None:
        """Write the FAISS index to disk."""
        idx_path = self._settings.faiss_index_path
        idx_path.mkdir(parents=True, exist_ok=True)
        self._store.save_local(str(idx_path))  # type: ignore[union-attr]
        logger.info("FAISS index persisted to %s", idx_path)


# ---------------------------------------------------------------------------
# Module-level singleton accessor
# ---------------------------------------------------------------------------
_vector_store: PolicyVectorStore | None = None


def get_vector_store() -> PolicyVectorStore:
    """Return (and lazily create) the singleton ``PolicyVectorStore``."""
    global _vector_store
    if _vector_store is None:
        _vector_store = PolicyVectorStore()
    return _vector_store
