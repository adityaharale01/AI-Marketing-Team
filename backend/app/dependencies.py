from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.oauth2 import get_current_user
from app.database import get_db
from app.models.business import Business
from app.models.user import User


def get_owned_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Business:
    """
    Resolve business_id from the path or query and confirm it belongs to
    the authenticated user. A business owned by someone else is reported as
    missing so IDs are not enumerable.
    """

    business = (
        db.query(Business)
        .filter(
            Business.id == business_id,
            Business.owner_id == current_user.id
        )
        .first()
    )

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    return business


def get_active_business(
    business_id: int | None = Query(
        None,
        description="Business to operate on. Defaults to the account's first business."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Business:
    """
    Business a request is scoped to. Omitting business_id keeps the previous
    single-business behaviour; supplying one switches every dependent query.
    """

    if business_id is None:
        if not current_user.businesses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have a business"
            )

        return current_user.businesses[0]

    return get_owned_business(
        business_id=business_id,
        db=db,
        current_user=current_user
    )
