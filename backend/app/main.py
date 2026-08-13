from fastapi import FastAPI
from sqlalchemy import text
from app.routers import business
from app.database import engine, Base
from app.routers.auth import router as auth_router
# Import all models
from app.models import User, Business, Product
from app.routers.users import router as user_router
from app.routers import sale
from app.routers import product
from app.routers import campaign
from app.routers import campaign_content
app = FastAPI(
    title="AI Marketing Team API",
    version="1.0.0"
)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(business.router)
app.include_router(sale.router)
app.include_router(product.router)
app.include_router(campaign.router)
app.include_router(campaign_content.router)
@app.get("/")
def home():
    return {
        "message": "AI Marketing Team Backend Running Successfully"
    }


@app.get("/test-db")
def test_database():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "message": "Database Connected Successfully"
    }

from app.auth.hashing import hash_password

'''@app.get("/hash")
def test_hash():

    password = "Admin123"

    hashed = hash_password(password)

    return {
        "Original": password,
        "Hashed": hashed
    }'''

'''from app.auth.hashing import verify_password

@app.get("/verify")
def verify():

    password = "Admin123"

    hashed = hash_password(password)

    result = verify_password(password, hashed)

    return {
        "Password Match": result
    }'''

'''from app.auth.oauth2 import create_access_token

@app.get("/token")
def generate_token():

    token = create_access_token(
        {"user_id": 1, "email": "admin@gmail.com"}
    )

    return {"access_token": token}


@app.get("/verify-token")
def verify():

    token = create_access_token(
        {"user_id": 1}
    )

    payload = verify_access_token(token)

    return payload'''