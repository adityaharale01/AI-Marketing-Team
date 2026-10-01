from fastapi import APIRouter
from app.services.ollama_service import generate_response
from app.services.rag_service import add_context, search_context
from fastapi import Depends
from sqlalchemy.orm import Session
from app.services.rag_service import search_context, build_context
from app.services.ollama_service import generate_response
from app.database import get_db
from app.services.rag_service import index_business_data
from app.services.business_agent import (
    ask_business_agent
)
router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)
from app.services.performance_service import (
    get_product_performance
)

from app.services.rag_service import (
    index_product_performance
)
from app.services.rag_service import search_business_context, build_context
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

@router.get("/test")
async def test_ai():

    response = await generate_response(
        "Explain marketing in one simple sentence."
    )

    return {
        "response": response
    }

@router.post("/rag/add")
async def add_rag_data():

    add_context(
        """
        Chocolate Cake is one of the best-selling products
        of ABC Bakery. Sales have increased recently.
        The bakery is planning a weekend promotion.
        """,
        "business_1_product_101"
    )

    return {
        "message": "Context added successfully"
    }

@router.get("/rag/search")
async def search_rag():

    result = search_context(
        "Which bakery product is performing well?"
    )

    return result

@router.post("/rag/index/{business_id}")
async def index_business(
    business_id: int,
    db: Session = Depends(get_db)
):

    return index_business_data(
        db,
        business_id
    )
@router.get("/rag/ask")
async def rag_ask(query: str):

    results = search_context(
        query,
        n_results=3
    )

    context = build_context(results)

    prompt = f"""
You are the Business Agent of an AI Marketing Team.

Answer the business owner's question using ONLY the verified
analytics provided below.

STRICT DATA-GROUNDING RULES:

1. Never invent facts.
2. Never infer customer demand from sales quantity alone.
3. Never say "high demand", "low demand", "strong demand",
   or similar demand claims unless the data explicitly contains
   a demand metric.
4. Never infer a cause from the available data.
5. If stock is 0, say "currently out of stock".
6. If previous_quantity is 0, say that there is no previous
   sales baseline and growth cannot be determined.
7. Do not describe a product as "best" or "highest performing"
   unless there is enough product data for a comparison.
8. If only one product is present, say that a comparison with
   other products is not possible.
9. Use exact numbers from the analytics when relevant.
10. If something cannot be determined from the data, explicitly
    say that it cannot be determined.
11. Do not add assumptions, explanations, or causes that are not
    present in the data.

VERIFIED BUSINESS ANALYTICS:
{analytics}

BUSINESS OWNER QUESTION:
{query}

Give a concise, factual business answer.
"""

    response = await generate_response(prompt)

    return {
        "query": query,
        "context": context,
        "response": response
    }

@router.get("/performance/{business_id}")
async def product_performance(
    business_id: int,
    db: Session = Depends(get_db)
):
    return get_product_performance(
        db,
        business_id
    )

@router.post("/rag/index-performance/{business_id}")
async def index_performance(
    business_id: int,
    db: Session = Depends(get_db)
):
    return index_product_performance(
        db,
        business_id
    )

from app.services.business_analytics_service import (
    get_business_analytics
)

@router.get("/business-analytics/{business_id}")
async def business_analytics(
    business_id: int,
    db: Session = Depends(get_db)
):
    try:
        return get_business_analytics(
            db,
            business_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.post("/business-agent")
async def business_agent(
    business_id: int,
    query: str,
    db: Session = Depends(get_db)
):
    try:
        result = await ask_business_agent(
            db=db,
            business_id=business_id,
            query=query
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.get("/rag/search/{business_id}")
async def search_business_rag(
    business_id: int,
    query: str
):
    results = search_business_context(
        query=query,
        business_id=business_id,
        n_results=3
    )

    context = build_context(results)

    return {
        "business_id": business_id,
        "query": query,
        "context": context,
        "results": results
    }
