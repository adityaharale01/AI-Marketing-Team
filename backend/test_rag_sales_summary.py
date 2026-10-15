from app.services.rag_service import (
    search_business_context,
    build_context
)

query = "Which products are declining?"

results = search_business_context(
    query=query,
    business_id=2,
    n_results=5,
    context_type="sales_summary"
)

print("\n===== RAG SALES SUMMARY =====\n")

print(build_context(results))