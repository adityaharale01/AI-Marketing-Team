from pathlib import Path
from typing import Optional
import os
import json
import base64
import urllib.error
import urllib.request

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.oauth2 import get_current_user
from app.database import get_db
from app.ai.agnets.marketing_agent import MarketingAgent

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

router = APIRouter(
    prefix="/marketing-agent",
    tags=["Marketing Agent"],
)

CLOUDFLARE_MODEL = "@cf/black-forest-labs/flux-1-schnell"
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4/accounts"


# --------------------------------------------------
# Campaign request schema
# --------------------------------------------------

class GenerateCampaignRequest(BaseModel):
    campaign_name: str
    goal: str
    platform: str
    target_audience: str
    offer: Optional[str] = None
    budget: Optional[float] = None
    business_id: int


# --------------------------------------------------
# Poster request schema
# --------------------------------------------------

class GeneratePosterRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=2048)
    steps: int = Field(default=4, ge=1, le=8)

    business_name: Optional[str] = Field(default=None, max_length=150)
    business_category: Optional[str] = Field(default=None, max_length=100)

    product_name: Optional[str] = Field(default=None, max_length=150)
    product_description: Optional[str] = Field(default=None, max_length=500)

    campaign_name: Optional[str] = Field(default=None, max_length=150)
    campaign_goal: Optional[str] = Field(default=None, max_length=500)
    target_audience: Optional[str] = Field(default=None, max_length=500)

    platform: str = Field(default="Instagram", max_length=100)
    offer: Optional[str] = Field(default=None, max_length=300)


# --------------------------------------------------
# Prompt builder — FIXED 2048 CHARACTER LIMIT
# --------------------------------------------------

def build_artwork_prompt(payload: GeneratePosterRequest) -> str:
    """
    Build a campaign-specific image prompt that never exceeds
    Cloudflare's 2048-character prompt limit.
    """

    instructions = (
        "Create premium commercial advertising artwork for the specified "
        "business and campaign. Make the relevant product the visual focus. "
        "Use professional lighting, attractive composition, suitable colors "
        "and a polished commercial photography style. Match the target "
        "audience and campaign objective. Leave clean negative space for "
        "promotional text to be added separately. Artwork only: no text, "
        "letters, numbers, logos, watermarks, labels, signs or fake writing."
    )

    fields = [
        ("Business", payload.business_name),
        ("Category", payload.business_category),
        ("Product", payload.product_name),
        ("Product details", payload.product_description),
        ("Campaign", payload.campaign_name),
        ("Goal", payload.campaign_goal),
        ("Audience", payload.target_audience),
        ("Platform", payload.platform),
        ("Offer", payload.offer),
        ("Visual direction", payload.prompt),
    ]

    # Leave room for instructions and newline separators.
    available = 2048 - len(instructions) - 1
    context_lines = []

    for label, value in fields:
        if value and available > 0:
            # Trim each field before adding it to the final prompt.
            line = f"{label}: {value.strip()}"
            line = line[:available]

            if line:
                context_lines.append(line)
                available -= len(line) + 1

    context = "\n".join(context_lines)
    final_prompt = f"{context}\n{instructions}" if context else instructions

    # Final safety check.
    if len(final_prompt) > 2048:
        final_prompt = final_prompt[:2048]

    return final_prompt


# --------------------------------------------------
# Cloudflare image generation helper
# --------------------------------------------------

def generate_cloudflare_image(prompt: str, steps: int) -> str:
    """
    Call Cloudflare FLUX Schnell and return the image as base64.
    """

    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")

    if not account_id or not api_token:
        raise HTTPException(
            status_code=500,
            detail=(
                "Cloudflare credentials are missing. "
                "Check CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN "
                "in backend/.env."
            ),
        )

    # Never send an oversized prompt to Cloudflare.
    if len(prompt) > 2048:
        raise HTTPException(
            status_code=400,
            detail="Image prompt exceeds the 2048-character limit.",
        )

    url = (
        f"{CLOUDFLARE_API_BASE}/{account_id}"
        f"/ai/run/{CLOUDFLARE_MODEL}"
    )

    request_body = json.dumps({
        "prompt": prompt,
        "steps": steps,
    }).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=request_body,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_data = response.read()

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")

        # Log provider details on the server, not the API token.
        print(f"Cloudflare image API error ({exc.code}): {error_body}")

        try:
            error_json = json.loads(error_body)
            errors = error_json.get("errors", [])
            provider_message = "; ".join(
                str(item.get("message", item))
                if isinstance(item, dict)
                else str(item)
                for item in errors
            )
        except (json.JSONDecodeError, AttributeError):
            provider_message = ""

        if not provider_message:
            provider_message = "Cloudflare could not generate the image."

        raise HTTPException(
            status_code=502,
            detail=provider_message[:500],
        ) from exc

    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=504,
            detail="Cloudflare image generation timed out or is unavailable.",
        ) from exc

    try:
        result = json.loads(response_data)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Cloudflare returned an invalid response.",
        ) from exc

    if result.get("success") is False:
        errors = result.get("errors", [])
        message = "; ".join(
            str(item.get("message", item))
            if isinstance(item, dict)
            else str(item)
            for item in errors
        )

        raise HTTPException(
            status_code=502,
            detail=message or "Cloudflare image generation failed.",
        )

    # Some Cloudflare responses return image bytes directly;
    # others return a JSON object containing an image field.
    content_type = "image/jpeg"

    if isinstance(result, dict):
        image_value = result.get("result", result)

        if isinstance(image_value, dict):
            image_value = (
                image_value.get("image")
                or image_value.get("data")
                or image_value.get("b64_json")
            )

        if isinstance(image_value, str):
            image_b64 = image_value

        elif isinstance(image_value, list) and image_value:
            first_item = image_value[0]

            if isinstance(first_item, str):
                image_b64 = first_item
            elif isinstance(first_item, dict):
                image_b64 = (
                    first_item.get("image")
                    or first_item.get("data")
                    or first_item.get("b64_json")
                )
            else:
                image_b64 = None
        else:
            image_b64 = None
    else:
        image_b64 = None

    if not image_b64:
        raise HTTPException(
            status_code=502,
            detail="Cloudflare returned no usable image data.",
        )

    # Validate that the returned value is valid base64.
    try:
        base64.b64decode(image_b64, validate=True)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Cloudflare returned invalid image data.",
        ) from exc

    return f"data:{content_type};base64,{image_b64}"


# --------------------------------------------------
# Generate campaign using local Ollama LLM
# --------------------------------------------------

@router.post("/generate")
async def generate_campaign(
    payload: GenerateCampaignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await MarketingAgent.generate(
        db=db,
        owner_id=current_user.id,
        payload=payload,
    )


# --------------------------------------------------
# Generate poster artwork using Cloudflare
# --------------------------------------------------

@router.post("/generate-poster")
def generate_poster(
    payload: GeneratePosterRequest,
    current_user=Depends(get_current_user),
):
    artwork_prompt = build_artwork_prompt(payload)

    image_data_url = generate_cloudflare_image(
        prompt=artwork_prompt,
        steps=payload.steps,
    )

    return {
        "image_data_url": image_data_url,
        "prompt_used": artwork_prompt,
    }


# --------------------------------------------------
# Demo publish campaign
# --------------------------------------------------

@router.post("/{campaign_id}/publish-demo")
def publish_campaign_demo(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return MarketingAgent.publish_demo(
        db=db,
        owner_id=current_user.id,
        campaign_id=campaign_id,
    )