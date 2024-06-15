import json
import os
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from IPython.display import display, Image as IPImage
import textwrap
from imgurpython import ImgurClient
import base64

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
    """Retrieve a random inspirational quote from the Quotable API."""
    url = "https://api.quotable.io/random"
    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        raise APIError(f"Failed to retrieve quote: {response.text}", response.status_code)

    data = response.json()
    quote = data["content"]
    return quote


def overlay_text_on_image(image_url, quote):
    """Overlay the quote text on the image."""
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))

    draw = ImageDraw.Draw(image)
    try:
        font_path = os.getenv('ARIAL_FONT_PATH')
        font = ImageFont.truetype(font_path, 100)  
    except IOError:
        font = ImageFont.load_default()  

    max_width = image.width - 40  
    wrapped_text = textwrap.fill(quote, width=40)  
    lines = wrapped_text.split('\n')
    text_height = font.size * len(lines)
    text_position = (20, 20)
    margin = 10
    x1, y1 = text_position
    x2 = x1 + max_width + 2 * margin
    y2 = y1 + text_height + 2 * margin
    draw.rectangle([(x1, y1), (x2, y2)], fill="black")
    current_y = y1 + margin
    for line in lines:
        draw.text((x1 + margin, current_y), line, font=font, fill="white")
        current_y += font.size

    output = BytesIO()
    image.save(output, format="JPEG")
    output.seek(0)

    return output


def send_to_teams(image_data):
    """Send the image with quote to a Microsoft Teams channel."""
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    headers = {
        "Content-Type": "application/json"
    }
    image = Image.open(image_data)
    image.thumbnail((700, 700))  
    
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    image_url = f"data:image/jpeg;base64,{image_base64}"
    
    
    adaptive_card = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.3",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Send by Anna Gaplanyan:",
                            "weight": "Bolder",
                            "size": "Medium"
                        },
                        {
                            "type": "Image",
                            "url": image_url,
                            "width": "700px",  
                            "height": "700px",  
                            "style": "Default"
                        }
                    ]
                }
            }
        ]
    }
    
    response = requests.post(webhook_url, headers=headers, data=json.dumps(adaptive_card))
    return response.text


def main():
    today = datetime.now().strftime("%A")
    if today == "Wednesday":
        image_url = get_image(query="toad")
        quote = "It's Wednesday, my dudes"
    else:
        image_url = get_image()
        quote = get_quote()

    image_data = overlay_text_on_image(image_url, quote)
    result = send_to_teams(image_data)
    


if __name__ == "__main__":
    main()
