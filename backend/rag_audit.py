"""Read-only audit for the project's persistent ChromaDB collection.

Run from the backend project root with the backend virtualenv active:
    python rag_audit.py
This script does not modify, delete, or re-index any data.
"""
from collections import Counter
from pathlib import Path
import json
import os
import sys

try:
    import chromadb
except ImportError:
    print("ERROR: chromadb is not installed in this Python environment.")
    sys.exit(1)

PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")).resolve()
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "business_knowledge")

print("=== ChromaDB RAG audit (READ ONLY) ===")
print(f"Working directory : {Path.cwd()}")
print(f"Persistent path   : {PERSIST_DIR}")
print(f"Path exists       : {PERSIST_DIR.exists()}")
print(f"Collection name   : {COLLECTION_NAME}")

if not PERSIST_DIR.exists():
    print("\nWARNING: This path does not exist. The running app may be using a different working directory/path.")

try:
    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    names = [c.name for c in client.list_collections()]
    print(f"Collections       : {names}")
    if COLLECTION_NAME not in names:
        print(f"\nERROR: collection '{COLLECTION_NAME}' not found in this path.")
        print("Do not create/re-index anything yet; confirm the app's actual path first.")
        sys.exit(2)
    collection = client.get_collection(COLLECTION_NAME)
    count = collection.count()
    print(f"Document count    : {count}")
    print(f"Collection metadata: {json.dumps(collection.metadata, default=str)}")
    if count == 0:
        print("\nRESULT: Collection is empty.")
        sys.exit(0)

    type_counts = Counter()
    business_counts = Counter()
    id_prefix_counts = Counter()
    missing_doc = 0
    missing_metadata = 0
    sample_by_type = {}
    offset = 0
    batch_size = 1000
    while offset < count:
        batch = collection.get(
            limit=min(batch_size, count - offset),
            offset=offset,
            include=["metadatas", "documents"],
        )
        ids = batch.get("ids") or []
        docs = batch.get("documents") or []
        metas = batch.get("metadatas") or []
        for i, doc_id in enumerate(ids):
            doc = docs[i] if i < len(docs) else None
            meta = metas[i] if i < len(metas) else None
            if not doc:
                missing_doc += 1
            if not meta:
                missing_metadata += 1
                meta = {}
            context_type = str(meta.get("context_type", "<missing>"))
            business_id = str(meta.get("business_id", "<missing>"))
            type_counts[context_type] += 1
            business_counts[business_id] += 1
            id_prefix_counts[str(doc_id).split("_")[0]] += 1
            if context_type not in sample_by_type:
                sample_by_type[context_type] = {
                    "id": doc_id,
                    "business_id": business_id,
                    "text_preview": (doc or "")[:220].replace("\n", " "),
                }
        offset += len(ids)
        if not ids:
            break

    print("\nDocuments by context_type:")
    for key, value in sorted(type_counts.items()):
        print(f"  {key}: {value}")
    print("\nDocuments by business_id:")
    for key, value in sorted(business_counts.items(), key=lambda kv: kv[0]):
        print(f"  {key}: {value}")
    print(f"\nDocuments missing text: {missing_doc}")
    print(f"Documents missing metadata: {missing_metadata}")
    print("\nSample document per context_type:")
    print(json.dumps(sample_by_type, indent=2, ensure_ascii=False))
    print("\nNext checks:")
    print("1. Confirm the path above matches the path used by app.services.rag_service.")
    print("2. Compare per-business counts with PostgreSQL products, sales, campaigns and campaign contents.")
    print("3. If counts are unexpectedly low, investigate index invocation before rebuilding anything.")
except Exception as exc:
    print(f"\nAUDIT FAILED: {type(exc).__name__}: {exc}")
    sys.exit(3)
