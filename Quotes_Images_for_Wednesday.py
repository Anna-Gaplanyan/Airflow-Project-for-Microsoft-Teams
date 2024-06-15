import json
import os
from datetime import datetime

import requests


class APIError(Exception):
    """Custom exception for API request errors."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


def get_image(query="curated"):
    """Retrieve the URL of an image from the Pexels API."""
    access_key = os.getenv("PEXELS_API_KEY")
    headers = {"Authorization": access_key}

    if query == "toad":
        url = "https://api.pexels.com/v1/search?query=toad"
    else:
        url = "https://api.pexels.com/v1/curated"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise APIError(f"Failed to retrieve image: {response.text}", response.status_code)

    image_url = response.json()["photos"][0]["src"]["original"]
    return image_url


def get_quote():
    """Retrieve a daily inspirational quote from the Quotes API."""
    api_key = os.getenv("QUOTES_API_KEY")
    url = f"https://quotes.rest/qod.json?category=inspire&api_key={api_key}"
    response = requests.get(url)

    if response.status_code != 200:
        raise APIError(f"Failed to retrieve quote: {response.text}", response.status_code)

    quote = response.json()["contents"]["quotes"][0]["quote"]
    return quote


def send_to_teams(image_url, quote):
    """Send the retrieved image and quote to a Microsoft Teams channel."""
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    headers = {
        "Content-Type": "application/json"
    }
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Daily Inspiration",
        "sections": [{
            "activityTitle": "Send by Anna Gaplanyan:",
            "text": quote,
            "images": [{
                "image": image_url
            }]
        }]
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(message))
    return response.text


def main():
    today = datetime.now().strftime("%A")
    if today == "Wednesday":
        image_url = get_image(query="toad")
        quote = "It's Wednesday, my dudes"
    else:
        image_url = get_image()
        quote = get_quote()

    result = send_to_teams(image_url, quote)
    print(result)


if __name__ == "__main__":
    main()
