import httpx
import os
import asyncio
import aiofiles

#Method to call Freepik AI image generation API
async def generate_image_freepik(prompt: str,fileName: str) -> str:
    #aspect ratio options : square_1_1, classic_4_3, traditional_3_4, 
    # widescreen_16_9, social_story_9_16, smartphone_horizontal_20_9
    #  smartphone_vertical_9_20, standard_3_2, portrait_2_3, \
    # horizontal_2_1, vertical_1_2, social_5_4, social_post_4_

    url = "https://api.freepik.com/v1/ai/mystic"

    payload = {
        "prompt": prompt,
        "webhook_url": "https://www.example.com/webhook",
        "resolution": "1k",
        "aspect_ratio": "square_1_1",
        "model": "realism",
        "creative_detailing": 33,
        "engine": "automatic",
        "fixed_generation": False,
        "filter_nsfw": True
    }
    headers = {
        "x-freepik-api-key": os.environ["FREEPIK_API_KEY"] ,
        "Content-Type": "application/json"
    }

    #use httpx to make async post request
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    #Extract the task id fro response in data property
    task_id = response.json().get("data", {}).get("task_id")

    #Call the status endpoint to get the image url using the task id , call every 5 seconds until the status is completed
    url = f"https://api.freepik.com/v1/ai/mystic/{task_id}"

    while True:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
            #On timeout exception only , we will allow another request to go through
            except httpx.ReadTimeout as e:
                print(f"An error occurred while requesting {e.request.url!r}.")
                await asyncio.sleep(5)
                continue
        status = response.json().get("data", {}).get("status")
        if status == "COMPLETED":
            break
        elif status == "FAILED":
            return ""
        else:
            await asyncio.sleep(5)
    
    #Get the image url from the response , inside data , inside generated property which is an array of string
    image_url = response.json().get("data", {}).get("generated", [])[0]
    
    #Save the image , and return the absolute path
    async with httpx.AsyncClient() as client:
        image_response = await client.get(image_url)

    image_path = os.path.abspath(fileName)

    print(f"Saving image to {image_path}")  
    
    async with aiofiles.open(image_path, "wb") as f:
        await f.write(image_response.content)
    
    return image_path