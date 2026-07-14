"""
KSP Crime Analytics — LLM Provider
===================================
Configures the Ollama-hosted LLM and embedding model.
All AI components import their LLM/embed instances from here.
"""

from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

# ============================================================
# LLM — Ollama (Local, Privacy-Safe)
# ============================================================
# Using llama3.2 (3B) for speed on Mac.
# Switch to llama3.1:8b or mistral for higher quality.

llm = Ollama(
    model="llama3.2",
    base_url="http://localhost:11434",
    temperature=0.1,         # Low temp for factual SQL/analytical queries
    request_timeout=120.0,
    context_window=4096,
)

# ============================================================
# Embedding Model — Local HuggingFace (No API needed)
# ============================================================
# all-MiniLM-L6-v2 is small (80MB), fast, and good for semantic search.
# It runs entirely on CPU — no GPU needed.

embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder="./.cache/embeddings",
)

# ============================================================
# Set as global defaults for LlamaIndex
# ============================================================
Settings.llm = llm
Settings.embed_model = embed_model
Settings.chunk_size = 512
Settings.chunk_overlap = 50
