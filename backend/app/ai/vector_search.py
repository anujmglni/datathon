"""
KSP Crime Analytics — Vector Search (RAG over BriefFacts)
==========================================================
Embeds FIR case summaries (BriefFacts) into a ChromaDB vector store
for semantic similarity search. This enables queries like:
    "Find cases with a similar modus operandi involving break-in through roof"
    "Cases where the accused used a knife near a school"
"""

import chromadb
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from sqlalchemy import create_engine, text

from app.config import settings

# Persistent ChromaDB storage
CHROMA_PATH = "./data/chroma_db"
_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _chroma_client.get_or_create_collection(
    name="crime_brieffacts",
    metadata={"hnsw:space": "cosine"},
)

# Vector store + index (lazy initialized)
_vector_index = None


def _load_documents_from_db() -> list[Document]:
    """Load BriefFacts from PostgreSQL and convert to LlamaIndex Documents."""
    engine = create_engine(settings.sync_database_url, echo=False)

    query = text("""
        SELECT
            cm.casemasterid,
            cm.crimeno,
            cm.caseno,
            cm.crimeregistereddate,
            cm.brieffacts,
            cm.latitude,
            cm.longitude,
            d.districtname,
            u.unitname AS station_name,
            csh.crimeheadname AS crime_type,
            ch.crimegroupname AS crime_group,
            csm.casestatusname AS case_status
        FROM casemaster cm
        LEFT JOIN unit u ON cm.policestationid = u.unitid
        LEFT JOIN district d ON u.districtid = d.districtid
        LEFT JOIN crimesubhead csh ON cm.crimeminorheadid = csh.crimesubheadid
        LEFT JOIN crimehead ch ON cm.crimemajorheadid = ch.crimeheadid
        LEFT JOIN casestatusmaster csm ON cm.casestatusid = csm.casestatusid
        WHERE cm.brieffacts IS NOT NULL AND cm.brieffacts != ''
    """)

    documents = []
    with engine.connect() as conn:
        result = conn.execute(query)
        for row in result:
            # Build a rich text document from the case data
            doc_text = (
                f"Crime Number: {row.crimeno}\n"
                f"Case Number: {row.caseno}\n"
                f"Registration Date: {row.crimeregistereddate}\n"
                f"District: {row.districtname}\n"
                f"Police Station: {row.station_name}\n"
                f"Crime Type: {row.crime_type} ({row.crime_group})\n"
                f"Status: {row.case_status}\n"
                f"Brief Facts: {row.brieffacts}"
            )

            metadata = {
                "case_id": row.casemasterid,
                "crime_no": row.crimeno,
                "case_no": str(row.caseno) if row.caseno else "",
                "district": row.districtname or "",
                "station": row.station_name or "",
                "crime_type": row.crime_type or "",
                "crime_group": row.crime_group or "",
                "status": row.case_status or "",
                "date": str(row.crimeregistereddate),
            }

            documents.append(Document(
                text=doc_text,
                metadata=metadata,
                doc_id=f"case_{row.casemasterid}",
            ))

    return documents


def build_vector_index(force_rebuild: bool = False) -> VectorStoreIndex:
    """Build or load the vector index from ChromaDB."""
    global _vector_index

    if _vector_index is not None and not force_rebuild:
        return _vector_index

    # Check if collection already has data
    if _collection.count() > 0 and not force_rebuild:
        print(f"📦 Loading existing vector index ({_collection.count()} documents)")
        vector_store = ChromaVectorStore(chroma_collection=_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        _vector_index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context,
        )
    else:
        print("🔨 Building vector index from database...")
        documents = _load_documents_from_db()
        print(f"   Loaded {len(documents)} case documents")

        vector_store = ChromaVectorStore(chroma_collection=_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        _vector_index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True,
        )
        print(f"✅ Vector index built with {len(documents)} documents")

    return _vector_index


async def query_vector(question: str, top_k: int = 5) -> dict:
    """
    Perform semantic search over BriefFacts.
    Returns the most similar cases and a synthesized answer.
    """
    try:
        index = build_vector_index()
        query_engine = index.as_query_engine(
            similarity_top_k=top_k,
            response_mode="tree_summarize",
        )

        response = query_engine.query(question)

        # Extract source cases from the response
        source_cases = []
        for node in response.source_nodes:
            source_cases.append({
                "case_id": node.metadata.get("case_id"),
                "crime_no": node.metadata.get("crime_no"),
                "district": node.metadata.get("district"),
                "crime_type": node.metadata.get("crime_type"),
                "status": node.metadata.get("status"),
                "date": node.metadata.get("date"),
                "relevance_score": round(node.score, 3) if node.score else None,
                "excerpt": node.text[:300] + "..." if len(node.text) > 300 else node.text,
            })

        return {
            "success": True,
            "answer": str(response),
            "source_cases": source_cases,
            "source": "vector-search",
        }

    except Exception as e:
        return {
            "success": False,
            "answer": f"Vector search failed: {str(e)}",
            "source_cases": [],
            "source": "vector-search",
        }
