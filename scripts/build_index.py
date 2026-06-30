"""
Build FAISS Index Script.

Reads all Markdown policy documents from ``data/policies/``,
chunks them, generates embeddings, and persists the FAISS index.

Usage:
    python scripts/build_index.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings
from app.rag.vector_store import PolicyVectorStore
from app.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("scripts.build_index")


def main() -> None:
    """Build the FAISS vector index from policy documents."""
    settings = get_settings()
    policies_dir = settings.policies_path

    logger.info("Building FAISS index from policies in %s", policies_dir)

    if not policies_dir.exists():
        logger.error("Policies directory does not exist: %s", policies_dir)
        sys.exit(1)

    md_files = list(policies_dir.glob("*.md"))
    if not md_files:
        logger.error("No .md files found in %s", policies_dir)
        sys.exit(1)

    logger.info("Found %d policy documents: %s", len(md_files), [f.name for f in md_files])

    store = PolicyVectorStore()
    num_chunks = store.build_index(policies_dir)

    logger.info("FAISS index built successfully — %d chunks indexed", num_chunks)
    logger.info("Index saved to: %s", settings.faiss_index_path)


if __name__ == "__main__":
    main()
