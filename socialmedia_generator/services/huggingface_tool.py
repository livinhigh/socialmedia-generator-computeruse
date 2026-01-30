import os
from huggingface_hub import AsyncInferenceClient
from openai import AsyncOpenAI
import anthropic


#Method that accepts a prompt and generates a text response using duckduckgo search tool and a model from Huggingface Hub
#Make it async
async def generate_text_response(prompt: str) -> str:    
    client = AsyncOpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"],
    )

    completion = await client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct:novita",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return str(completion.choices[0].message.content)

async def generate_text_response_anthropic(prompt: str) -> str:
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return str(message.content)

#Method that accepts a prompt and generates an image using an image generation tool from Huggingface Hub    
async def generate_image_returnpath(prompt: str,fileName: str) -> str:    
    client = AsyncInferenceClient(
        provider="auto",
        api_key=os.environ["HF_TOKEN"],
    )
    image_path = os.path.abspath(fileName)
    # output is a PIL.Image object
    image = await client.text_to_image(
        prompt=prompt,
        model="stabilityai/stable-diffusion-3.5-medium",
    )
    image.save(image_path)

    return image_path

