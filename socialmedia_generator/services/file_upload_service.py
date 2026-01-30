import os
import aioboto3
from aiohttp import ClientError
from botocore.client import Config
import asyncio

#write a method to upload an image to digital ocean spaces
async def upload_image_to_storage(image_path: str) -> str:
    #generate a random file name
    import uuid
    file_name = str(uuid.uuid4()) + ".jpg"

    # 2. Initialize the Async Session
    session = aioboto3.Session()
    
    # aioboto3 requires using 'async with' for the client context
    async with session.client('s3',
                                  region_name=os.environ.get('DO_SPACES_REGION', 'sgp1'), # e.g., nyc3
                                  endpoint_url=os.environ.get('DO_SPACES_ENDPOINT', 'https://marketingtool-storage-sg.sgp1.digitaloceanspaces.com'),
                                  aws_access_key_id=os.environ.get('DO_SPACES_KEY'),
                                  aws_secret_access_key=os.environ.get('DO_SPACES_SECRET')) as client:
        try:
            # 3. Upload the file asynchronously
            await client.upload_file(
                image_path, 
                'marketingtool-storage-sg', 
                file_name, 
                ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/jpeg'}
            )
            
            # 4. Construct the correct Public URL
            # Use the provided endpoint (e.g. https://<bucket>.<region>.digitaloceanspaces.com)
            endpoint = os.environ.get('DO_SPACES_ENDPOINT', 'https://marketingtool-storage-sg.sgp1.digitaloceanspaces.com')
            # Ensure no trailing slash
            endpoint = endpoint.rstrip('/')
            url = f"{endpoint}/{file_name}"
            return url
            
        except ClientError as e:
            print(f"Upload failed: {e}")
            return ""

