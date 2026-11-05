from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.oauth2 import get_current_user
from app.database import get_db
from app.dependencies import get_owned_business
from app.models.business import Business
from app.models.user import User
from app.services.business_agent import ask_business_agent
from app.services.business_analytics_service import get_business_analytics
from app.services.ollama_service import generate_response
from app.services.performance_service import get_product_performance
from app.services.rag_service import (
    add_context,
    build_context,
    index_business_data,
    index_product_performance,
    search_business_context
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


class RagAddRequest(BaseModel):

    content: str = Field(..., min_length=1, max_length=5000)

    title: str | None = Field(default=None, max_length=200)


@router.get("/test")
async def test_ai(
    current_user: User = Depends(get_current_user)
):

    response = await generate_response(
        "Explain marketing in one simple sentence."
    )

    return {
        "response": response
    }

@router.post("/rag/add")
async def add_rag_data(
    payload: RagAddRequest,
    business: Business = Depends(get_owned_business)
):

    context = payload.content.strip()

    if payload.title:
        context = f"{payload.title}\n\n{context}"

    add_context(
        context=context,
        context_id=f"business_{business.id}_note_{hash(context) & 0xFFFFFFFF}",
        business_id=business.id,
        context_type="note"
    )

    return {
        "business_id": business.id,
        "message": "Context added successfully"
    }


@router.get("/rag/search")
async def search_rag(
    query: str,
    business: Business = Depends(get_owned_business)
):

    results = search_business_context(
        query=query,
        business_id=business.id,
        n_results=3
    )

    return {
        "business_id": business.id,
        "query": query,
        "context": build_context(results),
        "results": results
    }


@router.post("/rag/index/{business_id}")
async def index_business(
    db: Session = Depends(get_db),
    business: Business = Depends(get_owned_business)
):

    return index_business_data(
        db,
        business.id
    )


@router.get("/rag/ask")
async def rag_ask(
    query: str,
    db: Session = Depends(get_db),
    business: Business = Depends(get_owned_business)
):

    results = search_business_context(
        query=query,
        business_id=business.id,
        n_results=3
    )

    context = build_context(results)

    analytics = get_business_analytics(
        db=db,
        business_id=business.id
    )

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

RETRIEVED BUSINESS KNOWLEDGE:
{context}

VERIFIED BUSINESS ANALYTICS:
{analytics}

BUSINESS OWNER QUESTION:
{query}

Give a concise, factual business answer.
"""

    response = await generate_response(prompt)

    return {
        "business_id": business.id,
        "query": query,
        "context": context,
        "response": response
    }

@router.get("/performance/{business_id}")
async def product_performance(
    db: Session = Depends(get_db),
    business: Business = Depends(get_owned_business)
):
    return get_product_performance(
        db,
        business.id
    )

@router.post("/rag/index-performance/{business_id}")
async def index_performance(
    db: Session = Depends(get_db),
    business: Business = Depends(get_owned_business)
):
    return index_product_performance(
        db,
        business.id
    )

@router.get("/business-analytics/{business_id}")
async def business_analytics(
    db: Session = Depends(get_db),
    business: Business = Depends(get_owned_business)
):
    try:
        return get_business_analytics(
            db,
            business.id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.post("/business-agent")
async def business_agent(
    query: str,
    db: Session = Depends(get_db),
    business: Business = Depends(get_owned_business)
):
    try:
        result = await ask_business_agent(
            db=db,
            business_id=business.id,
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
    query: str,
    business: Business = Depends(get_owned_business)
):
    results = search_business_context(
        query=query,
        business_id=business.id,
        n_results=3
    )

    context = build_context(results)

    return {
        "business_id": business.id,
        "query": query,
        "context": context,
        "results": results
    }
