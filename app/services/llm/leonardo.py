import requests
import json
import time
from io import BytesIO
from PIL import Image

from config import settings


def image_generation(video_id, prompt):

    authorization = f"Bearer {settings.LEONARDO_API_KEY}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": authorization,
    }
    # Generate with Image to Image
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    payload = {
        "height": 720,
        "num_images": 1,
        "modelId": "b24e16ff-06e3-43eb-8d33-4416c2d75876",
        "prompt": prompt,
        "width": 1280,
        # "init_image_id": image_id,
        # "init_strength": 0.28,
        "guidance_scale": 9,
        "highResolution": True,
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Generation of Images using Image to Image:", response.status_code)
    # Get the generation of images
    generation_id = response.json()["sdGenerationJob"]["generationId"]
    url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
    time.sleep(20)
    response = requests.get(url, headers=headers)

    data = json.loads(response.text)
    # Extract the URL from the parsed JSON
    image_url_1 = data["generations_by_pk"]["generated_images"][0]["url"]
    print(image_url_1)
    response = requests.get(image_url_1)
    image = Image.open(BytesIO(response.content))
    image.save(f"./temp/{video_id}/thumbnail.jpg")
    return image_url_1
