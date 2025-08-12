import requests
import json

WEBFLOW_API_TOKEN = "eb15ebc98c646b196360f7124a63385888f970f63ce43aaa053de71afe6a49cd"  # Use your actual API token
SITE_ID = "54fbba52c90501f404480665"  # Replace with your actual site ID
COLLECTION_ID = "68802dbb82371135ef418874"  # Replace with your actual collection ID

headers = {
    "Authorization": f"Bearer {WEBFLOW_API_TOKEN}",
    "accept-version": "1.0.0",
    "Content-Type": "application/json"
}

# Example data for the page
data = {
    "items": [
        {
            "fieldData": {
                "name": "Homepage",
                "slug": "home",
                "hero-heading": "Welcome to Serenity Spa",
                "hero-subheading": "Relax, Rejuvenate, and Renew",
                "hero-image": {"url": "https://media.istockphoto.com/id/484234714/vector/example-free-grunge-retro-blue-isolated-stamp.jpg?s=612x612&w=0&k=20&c=97KgKGpcAKnn50Ubd8PawjUybzIesoXws7PdU_MJGzE="},  # Use your real image URL here
                "page-content": "<p>Welcome to Serenity Spa. Your wellness journey starts here.</p>",
                "about-heading": "About Us",
                "about-text": "<p>Serenity Spa is your go-to destination for relaxation and beauty treatments.</p>",
                "about-image": {"url": "https://media.istockphoto.com/id/484234714/vector/example-free-grunge-retro-blue-isolated-stamp.jpg?s=612x612&w=0&k=20&c=97KgKGpcAKnn50Ubd8PawjUybzIesoXws7PdU_MJGzE="},  # Use your real image URL here
                "cta-button-text": "Book Now",
                "cta-button-url": "/contact-us"
            }
        }
    ]
}

# Post request to Webflow API
response = requests.post(
    f"https://api.webflow.com/v2/collections/{COLLECTION_ID}/items",  # Correct API endpoint
    headers=headers,
    json=data
)

# Log the response for debugging
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")
