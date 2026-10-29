import os
import base64
import requests
from dotenv import load_dotenv

# Load backend/.env
load_dotenv()

account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
token = os.getenv("CLOUDFLARE_API_TOKEN")

if not account_id or not token:
    raise ValueError(
        "Cloudflare credentials not found. Check backend/.env"
    )

url = (
    f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
    "/ai/run/@cf/black-forest-labs/flux-1-schnell"
)

response = requests.post(
    url,
    headers={"Authorization": f"Bearer {token}"},
    json={
        "prompt": (
            "Professional bakery advertising artwork featuring "
            "a delicious chocolate cake, warm lighting, "
            "premium photography, no text"
        ),
        "steps": 4,
    },
    timeout=120,
)

response.raise_for_status()
data = response.json()

if not data.get("success"):
    raise RuntimeError(data.get("errors", data))

image_b64 = data["result"]["image"]

with open("test_poster.jpg", "wb") as f:
    f.write(base64.b64decode(image_b64))

print("Success! Saved test_poster.jpg")