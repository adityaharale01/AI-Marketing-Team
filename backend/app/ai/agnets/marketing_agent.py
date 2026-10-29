"""Marketing campaign generation using the local Ollama LLM."""
import json
import re
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.product import Product
from app.models.campaign import Campaign
from app.models.campaign_content import CampaignContent
from app.services.ollama_service import generate_response


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    return {
        "strategy": cleaned,
        "caption": cleaned[:1200],
        "hashtags": ["#SmallBusiness", "#ShopLocal", "#Marketing"],
        "poster_headline": "Discover something special",
        "poster_subtitle": "Made with care, just for you",
        "call_to_action": "Visit us today",
        "content_notes": "Review AI-generated text before publishing."
    }


def _text(value, default=""):
    if value is None:
        return default
    if isinstance(value, list):
        return " ".join(str(x) for x in value)
    return str(value).strip() or default


class MarketingAgent:
    @staticmethod
    async def generate(db: Session, owner_id: int, payload):
        business_query = db.query(Business).filter(
            Business.owner_id == owner_id, Business.is_active.is_(True)
        )
        if getattr(payload, "business_id", None) is not None:
            business_query = business_query.filter(Business.id == payload.business_id)
        business = business_query.order_by(Business.id.asc()).first()
        if not business:
            raise HTTPException(status_code=400, detail="Create a business profile before generating a campaign.")

        products = (
            db.query(Product)
            .filter(Product.business_id == business.id, Product.is_active.is_(True))
            .order_by(Product.product_name.asc()).limit(20).all()
        )
        facts = {
            "business": {
                "name": business.business_name,
                "type": business.business_type,
                "description": business.description or "",
                "city": business.city or ""
            },
            "products": [
                {"name": p.product_name, "category": p.category, "price": p.price,
                 "stock": p.stock, "description": p.description or ""}
                for p in products
            ]
        }
        name = _text(payload.campaign_name, f"{business.business_name} Marketing Campaign")[:150]
        goal = _text(payload.goal, "Increase awareness and engagement")
        platform = _text(payload.platform, "Instagram")[:100]
        offer = _text(payload.offer, "No specific offer or discount supplied")
        audience = _text(payload.target_audience, "Local customers interested in this business")
        prompt = f"""
You are Crumbwise, a practical marketing strategist for small businesses.
Use the business facts below. Never invent prices, discounts, sales figures, customer counts, or claims.
If no offer is provided, propose an angle that does not require a discount.
Return ONLY valid JSON with keys:
strategy (4-6 concise sentences with objective, audience, key message, content approach, timing and measurable KPI),
caption (platform-appropriate caption), hashtags (array of 5-10 strings),
poster_headline (short), poster_subtitle (short), call_to_action (short),
content_notes (assumptions or review note). Use simple language; no markdown fences.
BUSINESS FACTS: {json.dumps(facts, ensure_ascii=False)}
CAMPAIGN NAME: {name}
GOAL: {goal}
PLATFORM: {platform}
TARGET AUDIENCE: {audience}
OFFER FROM USER: {offer}
BUDGET INR: {payload.budget if payload.budget is not None else "not specified"}
"""
        try:
            raw = await generate_response(prompt)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Could not reach local Ollama. Start Ollama and confirm the configured model is installed.") from exc

        result = _parse_json(raw)
        strategy = _text(result.get("strategy"), "Share useful, consistent content that highlights the business and invites customers to take the next step.")
        caption = _text(result.get("caption"), f"Discover {business.business_name}. Visit us to learn more!")
        tags = result.get("hashtags", [])
        if not isinstance(tags, list):
            tags = re.findall(r"#[A-Za-z0-9_]+", str(tags))
        tags = [str(t).strip() if str(t).strip().startswith("#") else "#" + re.sub(r"\W+", "", str(t)) for t in tags if str(t).strip()]
        tags = (tags[:12] or ["#ShopLocal", "#SmallBusiness"])
        poster = {
            "headline": _text(result.get("poster_headline"), name)[:100],
            "subtitle": _text(result.get("poster_subtitle"), "Discover something special")[:160],
            "call_to_action": _text(result.get("call_to_action"), "Learn more")[:80]
        }
        notes = _text(result.get("content_notes"), "Review the campaign details before publishing.")

        today = date.today()
        campaign = Campaign(
            business_id=business.id, campaign_name=name, objective=goal[:255],
            target_audience=audience[:1000], platform=platform,
            start_date=today, end_date=today + timedelta(days=7),
            budget=payload.budget, status="draft", is_active=True
        )
        db.add(campaign)
        db.flush()
        records = [
            ("marketing_strategy", strategy),
            ("caption", caption),
            ("hashtags", " ".join(tags)),
            ("poster_text", json.dumps(poster, ensure_ascii=False)),
            ("content_notes", notes)
        ]
        for kind, text in records:
            db.add(CampaignContent(
                campaign_id=campaign.id, content_type=kind, platform=platform,
                content_text=text, created_by_ai=True, is_approved=False
            ))
        db.commit()
        db.refresh(campaign)
        return {
            "campaign_id": campaign.id,
            "business": {"id": business.id, "name": business.business_name, "type": business.business_type},
            "campaign_name": campaign.campaign_name, "objective": campaign.objective,
            "platform": platform, "target_audience": audience,
            "strategy": strategy, "caption": caption, "hashtags": tags,
            "poster": poster, "content_notes": notes, "status": "draft",
            "publish_mode": "demo_only",
            "message": "Campaign saved as a draft. No social-media platform was contacted."
        }

    @staticmethod
    def publish_demo(db: Session, owner_id: int, campaign_id: int):
        campaign = (
            db.query(Campaign)
            .join(Business, Campaign.business_id == Business.id)
            .filter(Campaign.id == campaign_id, Business.owner_id == owner_id)
            .first()
        )
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found for this business.")
        campaign.status = "active"
        db.add(CampaignContent(
            campaign_id=campaign.id, content_type="publish_demo",
            platform=campaign.platform,
            content_text=json.dumps({
                "mode": "demo_only", "simulated": True,
                "message": "Recorded locally; no post was sent to the social platform."
            }),
            created_by_ai=False, is_approved=True
        ))
        db.commit()
        return {
            "campaign_id": campaign.id, "status": "active",
            "simulated": True, "platform": campaign.platform,
            "message": "Demo published successfully. This is a local simulation, not a real social-media post."
        }
