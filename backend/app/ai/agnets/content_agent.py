from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.business_services import BusinessService
from app.services.campaign_service import CampaignService
from app.services.product_service import ProductService
from app.services.campaign_content_service import CampaignContentService
from app.services.ai_interaction_service import AIInteractionService

from app.schemas.campaign_content import CampaignContentCreate
from app.schemas.ai_interactions import AIInteractionCreate


class ContentAgent:
    """
    AI agent responsible for generating marketing content
    using business, product, campaign and user-request data.
    """

    SUPPORTED_CONTENT_TYPES = {
        "caption",
        "social_media_post",
        "reel_script",
        "poster_text",
        "whatsapp_message",
    }

    def __init__(self, llm_service):
        self.llm_service = llm_service

    def generate_content(
        self,
        db: Session,
        current_user,
        campaign_id: int,
        content_type: str,
        platform: str,
        user_prompt: str,
    ):
        """
        Generate marketing content for a campaign.
        """

        # ---------------------------------------------------------
        # 1. Validate request
        # ---------------------------------------------------------

        if not campaign_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign ID is required."
            )

        if not content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content type is required."
            )

        content_type = content_type.strip().lower()

        if content_type not in self.SUPPORTED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported content type: {content_type}. "
                    f"Supported types: "
                    f"{', '.join(sorted(self.SUPPORTED_CONTENT_TYPES))}"
                )
            )

        if not platform or not platform.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Platform is required."
            )

        if not user_prompt or not user_prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt is required."
            )

        platform = platform.strip()
        user_prompt = user_prompt.strip()

        # ---------------------------------------------------------
        # 2. Get authenticated user's business
        # ---------------------------------------------------------

        businesses = BusinessService.get_my_businesses(
            db=db,
            owner_id=current_user.id
        )

        if not businesses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No business found for the authenticated user."
            )

        # Current project allows the authenticated user to have
        # businesses. For now, use the first business.
        business = businesses[0]

        # ---------------------------------------------------------
        # 3. Get campaign belonging to user's business
        # ---------------------------------------------------------

        campaign = CampaignService.get_campaign(
            db=db,
            campaign_id=campaign_id,
            business_id=business.id
        )

        # ---------------------------------------------------------
        # 4. Verify campaign ownership
        # ---------------------------------------------------------

        if campaign.business_id != business.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this campaign."
            )

        # ---------------------------------------------------------
        # 5. Get products belonging to the business
        # ---------------------------------------------------------

        products = ProductService.get_products(
            db=db,
            business_id=business.id
        )

        # ---------------------------------------------------------
        # 6. Build contextual marketing prompt
        # ---------------------------------------------------------

        prompt = self._build_prompt(
            business=business,
            products=products,
            campaign=campaign,
            content_type=content_type,
            platform=platform,
            user_prompt=user_prompt
        )

        # ---------------------------------------------------------
        # 7. Generate content using LLM
        # ---------------------------------------------------------

        try:
            generated_content = self.llm_service.generate(
                prompt=prompt
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to generate marketing content."
            ) from exc

        if not generated_content:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The AI returned an empty response."
            )

        generated_content = generated_content.strip()

        if not generated_content:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The AI returned an empty response."
            )

        # ---------------------------------------------------------
        # 8. Save CampaignContent
        # ---------------------------------------------------------

        campaign_content_data = CampaignContentCreate(
            content_type=content_type,
            platform=platform,
            content_text=generated_content,
            created_by_ai=True,
            is_approved=False
        )

        CampaignContentService.create_content(
            db=db,
            campaign_id=campaign.id,
            business_id=business.id,
            content_data=campaign_content_data
        )

        # ---------------------------------------------------------
        # 9. Save AIInteraction
        # ---------------------------------------------------------

        interaction_data = AIInteractionCreate(
            agent_type="content_generation",
            user_query=user_prompt,
            ai_response=generated_content
        )

        AIInteractionService.create_interaction(
            db=db,
            user_id=current_user.id,
            business_id=business.id,
            interaction_data=interaction_data
        )

        # ---------------------------------------------------------
        # 10. Return clean response
        # ---------------------------------------------------------

        return {
            "agent_type": "content_generation",
            "content_type": content_type,
            "platform": platform,
            "content": generated_content
        }

    # =============================================================
    # PROMPT BUILDING
    # =============================================================

    def _build_prompt(
        self,
        business,
        products,
        campaign,
        content_type: str,
        platform: str,
        user_prompt: str,
    ) -> str:

        business_context = f"""
Business Name: {business.business_name}
Business Type: {business.business_type}
Business Description: {
    business.description or "Not provided"
}
"""

        product_context = self._build_product_context(products)

        campaign_context = f"""
Campaign Name: {campaign.campaign_name}
Campaign Objective: {campaign.objective}
Target Audience: {
    campaign.target_audience or "Not provided"
}
Campaign Platform: {campaign.platform}
Campaign Budget: {
    campaign.budget if campaign.budget is not None else "Not provided"
}
Campaign Start Date: {campaign.start_date}
Campaign End Date: {campaign.end_date}
"""

        content_instructions = self._get_content_type_instructions(
            content_type
        )

        return f"""
You are an expert marketing content generator.

Generate high-quality marketing content using the
business, products, campaign and user request provided below.

BUSINESS INFORMATION
{business_context}

PRODUCT INFORMATION
{product_context}

CAMPAIGN INFORMATION
{campaign_context}

REQUESTED PLATFORM
{platform}

REQUESTED CONTENT TYPE
{content_type}

USER REQUEST
{user_prompt}

CONTENT REQUIREMENTS
{content_instructions}

IMPORTANT RULES:
- Do not invent prices.
- Do not invent discounts.
- Do not invent product features.
- Do not invent business information.
- Do not make unsupported claims.
- Use only information provided in the context.
- Keep the content relevant to the campaign objective.
- Consider the target audience carefully.
- Follow the requested platform.
- Follow the requested content type.
- Follow the user's request.
- Return only the final marketing content.
"""

    def _build_product_context(self, products) -> str:

        if not products:
            return "No product information is currently available."

        product_lines = []

        for product in products:

            product_lines.append(
                f"""
Product Name: {product.product_name}
Category: {product.category}
Description: {
    product.description or "Not provided"
}
Price: {
    product.price if product.price is not None
    else "Not provided"
}
"""
            )

        return "\n".join(product_lines)

    def _get_content_type_instructions(
        self,
        content_type: str
    ) -> str:

        instructions = {

            "caption": """
Create an engaging social media caption.

Include:
- Strong opening hook
- Product/campaign value
- Clear call to action
- Relevant hashtags when appropriate

Keep it concise.
""",

            "social_media_post": """
Create an engaging social media marketing post.

Include:
- Attention-grabbing opening
- Relevant product/campaign information
- Value for the target audience
- Clear call to action
""",

            "reel_script": """
Create a short promotional reel script.

Structure:
1. Hook
2. Scene or visual suggestion
3. Voiceover/dialogue
4. Call to action

Keep the script suitable for a short promotional video.
""",

            "poster_text": """
Create concise promotional poster text.

It should be:
- Short
- Attention-grabbing
- Easy to read
- Promotional
- Call-to-action oriented
""",

            "whatsapp_message": """
Create a concise WhatsApp marketing message.

It should be:
- Conversational
- Friendly
- Promotional
- Easy to read
- Call-to-action oriented
"""
        }

        return instructions[content_type]