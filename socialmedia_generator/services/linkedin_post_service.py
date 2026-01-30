import requests
import asyncio
import httpx
import uuid
import aiofiles

# --- Configuration ---
ACCESS_TOKEN = ""
AUTHOR_URN = ""  # or urn:li:organization:ID
POST_TEXT = ""
API_VERSION = "" # Format: YYYYMM

headers1 = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Linkedin-Version": API_VERSION,
    "X-Restli-Protocol-Version": "2.0.0"
}


headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Linkedin-Version": API_VERSION,
    "X-Restli-Protocol-Version": "2.0.0"
}

async def post_to_linkedin(imageUrl: str,postText: str):
    #Get the organization id
    AUTHOR_URN = await get_organization_id()
    # STEP 1: Initialize the Image Upload
    print("Initializing image upload...")
    init_url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    init_data = {
        "initializeUploadRequest": {
            "owner": AUTHOR_URN
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(init_url, json=init_data, headers=headers)

    if response.status_code != 200:
        print(f"Failed to initialize: {response.text}")
        return

    init_res = response.json()
    upload_url = init_res['value']['uploadUrl']
    image_urn = init_res['value']['image']
    print(f"Image URN: {image_urn}")

    # STEP 2: Upload the Binary Image
    print("Uploading image file...")

    #Download the image from imageUrl 
    async with httpx.AsyncClient() as client:
        image_response = await client.get(imageUrl)
    
    #Save the image to a new temp folder with a random guid name , dont use IMAGE_PATH
    imagePath = "/tmp/" + str(uuid.uuid4()) + ".jpg"
    async with aiofiles.open(imagePath, "wb") as f:
        await f.write(image_response.content)



    with open(imagePath, "rb") as image_file:
        # Note: LinkedIn requires a binary PUT request for the image upload
        # No extra headers are needed for the upload URL itself usually
        async with httpx.AsyncClient() as client:
            upload_response = await client.put(upload_url, content=image_file.read())
        
    if upload_response.status_code not in [200, 201]:
        print(f"Failed to upload image: {upload_response.status_code}")
        return

    # STEP 3: Create the Post
    print("Creating the post...")
    post_url = "https://api.linkedin.com/rest/posts"
    post_data = {
        "author": AUTHOR_URN,
        "commentary": postText,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "id": image_urn,
                "altText": "A beautiful photo uploaded via API"
            }
        },
        "lifecycleState": "PUBLISHED"
    }

    async with httpx.AsyncClient() as client:
        create_post_response = await client.post(post_url, json=post_data, headers=headers)
    
    if create_post_response.status_code == 201:
        post_id = create_post_response.headers.get("x-restli-id")
        print(f"Success! Post created with ID: {post_id}")
    else:
        print(f"Failed to create post: {create_post_response.status_code}")
        print(create_post_response.text)

#write a method to get the organization id of the authenticated user
async def get_organization_id() -> str:
    # This endpoint finds organizations where you have access
    url1 = "https://api.linkedin.com/rest/organizationAcls?q=roleAssignee"

    async with httpx.AsyncClient() as client:
        response1 = await client.get(url1, headers=headers1)
    data1 = response1.json()
    print(f"Organization data: {data1}")
    if response1.status_code == 200:
        elements = data1.get("elements", [])
        if not elements:
            print("No organizations found. Ensure you are an admin of a LinkedIn Page.")
        for entry in elements:
            # The organization URN is usually in the 'organization' field
            org_urn = entry.get("organization")
            role = entry.get("role")
            print(f"Role: {role} | Organization URN: {org_urn}")
            return org_urn
    else:
        print(f"Error: {data1}")
    raise Exception("Could not retrieve organization ID")
