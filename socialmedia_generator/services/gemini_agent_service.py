"""
Gemini Agent Service - Orchestrates Google Gemini automation tasks.

"""
import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable, Union
import requests
from bs4 import BeautifulSoup
from socialmedia_generator.services import file_upload_service
from sqlalchemy.orm import Session as DBSession
from socialmedia_generator.services.post_service import PostService
from socialmedia_generator.database.post_models import MediaType, PostStatus
from socialmedia_generator.constants import ContentTypeConstants, FileConstants
from socialmedia_generator.helper.jsonhelper import parse_json_from_string
import socialmedia_generator.services.huggingface_tool as huggingface_tool
import socialmedia_generator.services.freepik_tool as freepik_tool
from socialmedia_generator.prompts import (
    IMAGE_GENERATION_PROMPT_TEMPLATE,
    TEXT_AND_IMAGE_GENERATION_PROMPT_TEMPLATE,
    get_step_description
)

logger = logging.getLogger(__name__)


class GeminiAgentService:
    """
    Service for orchestrating Google Gemini automation via computer-use agent.
    
    Manages the entire post generation workflow:
    - Data extraction from sources
    - Text variation generation
    - Image generation
    - WebSocket progress updates
    """
    
    def __init__(
        self,
        post_service: PostService,
        work_dir: str = "/tmp/post_generation"
    ):
        """
        Initialize Gemini agent service.
        
        Args:
            post_service: PostService instance
            work_dir: Working directory for temporary files
        """
        self.post_service = post_service
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.login_script_path = Path(__file__).resolve().parent.parent / "scripts" / FileConstants.GOOGLE_LOGIN_SCRIPT_NAME
        
        # Google credentials from environment
        self.google_email = os.getenv("GOOGLE_EMAIL")
        self.google_password = os.getenv("GOOGLE_PASSWORD")
        
        if not self.google_email or not self.google_password:
            logger.warning("Google credentials not found in environment variables")
    ProgressCallback = Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]]
    async def generate_post(
        self,
        db: DBSession,
        post_id: str,
        progress_callback: Optional[ProgressCallback] = None
    ) -> bool:
        """
        Main orchestration method for post generation.
        
        Args:
            db: Database session
            post_id: Post ID to generate
            progress_callback: Optional callback for progress updates (step, message)
        
        Returns:
            True if successful, False otherwise
        """
        # Get post object
        from socialmedia_generator.database.post_models import Post
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            logger.error(f"Post {post_id} not found")
            return False
            
        try:
        
            # Step 2: Generate text variations using Gemini
            await self._send_progress(progress_callback, "generating_text",
                                    "Generating text variations...")                
            
            #Fetch data sources to build context from DB , iterate through all sources , only process for links
            data_sources = self.post_service.get_data_sources(db, str(post.id))
            extracted_contexts = []
            for idx, source in enumerate(data_sources, 1):
                source_type = source["type"]
                content = source["content"]
                
                await self._send_progress(
                    progress_callback, "extracting_context",
                    f"Processing source {idx}/{len(data_sources)}: {source_type}",
                    source_num=idx, source_type=source_type
                )
                
                if source_type == "link":
                    # Extract from URL
                    extracted_text = self.get_text_content_from_website(content)
                    if extracted_text:
                        extracted_contexts.append(extracted_text)
                elif source_type == "text":
                    extracted_contexts.append(content)
                    
            #convert extracted_contexts to string
            context = "\n\n---\n\n".join(extracted_contexts)

            #use generate text variation from hugging face tool
            text_variations_raw = await huggingface_tool.generate_text_response(
                TEXT_AND_IMAGE_GENERATION_PROMPT_TEMPLATE.format(
                    content_type=ContentTypeConstants.CONTENT_TYPE_MAP.get(post.content_type.value, "Long Form"),
                    context=context,
                    num_variations=post.text_variations_count,
                    image_num_variations=post.media_variations_count,
                    language_tone=post.language_tone
                )
            )
            print(f"Raw text variations response: {text_variations_raw}")

            text_variations_raw = text_variations_raw.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').replace('#','(Hashtag)')

            text_variations = parse_json_from_string(text_variations_raw)

            for var_data in text_variations.get("variations", []):
                text_id = self.post_service.add_text_variation(
                    db,
                    post_id,
                    var_data["variation_number"],
                    var_data["text_content"],
                    {"prompts": []}
                )
                
                if text_id:                        
                    await self._send_progress(
                        progress_callback, "generating_text",
                        f"Generated text variation {var_data['variation_number']}",
                        variation_num=var_data['variation_number']
                    )

            mediaCount =1
            if post.media_content_needed.value in ["image", "both"]:
                await self._send_progress(progress_callback, "generating_media",
                                        "Generating images...")
                for var_data in text_variations.get("image_prompts", []):
                    #pass all the text_content in text_variations as post_text to give context to image generation
                    image_path = await freepik_tool.generate_image_freepik(
                            prompt=IMAGE_GENERATION_PROMPT_TEMPLATE.format(
                                post_text=", ".join([v["text_content"] for v in text_variations.get("variations", [])]),
                                image_prompt=str(var_data)
                            ),
                            fileName=f"{self.work_dir}/generated_image_post_{post.id}.png"
                    )
                    
                    image_url = await file_upload_service.upload_image_to_storage(image_path)
                    
                    self.post_service.add_media_content(
                        db,
                        post_id,
                        MediaType.IMAGE,
                        mediaCount,
                        image_url,
                        str(var_data)
                    )
                    mediaCount += 1
            
            #Generate the completed message with a json of text variations and image urls
            self.post_service.update_post_status(
                db, str(post.id), PostStatus.COMPLETED,
                current_step="Post generation completed"
            )

            #Call get_generated_post_content and generate json to send in completed message
            generated_content = self.get_generated_post_content(db, str(post.id))
            await self._send_progress(progress_callback, "completed", 
                                    "Generated Post Content", 
                                    content=generated_content)
            return True
            
        except Exception as e:
            logger.error(f"Error generating post {post.id}: {e}", exc_info=True)
            await self._update_post_error(db, str(post.id), str(e))
            return False
    
    #A method that gets the contents of a website using trafilatura
    def get_text_content_from_website(self, url: str) -> str:
        """
        Extract text content from a website using trafilatura.
        
        Args:
            url: URL of the website to extract from
        Returns:
            Extracted text content as string
        """
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted_text = trafilatura.extract(downloaded)
            return extracted_text if extracted_text else ""
        return ""


    #A method that returns the generated text varaitions , along with variation ID
    #Also the image variations along with image prompts and variation ID
    def get_generated_post_content(
        self,
        db: DBSession,
        post_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve generated text and media content for a post.
        
        Args:
            db: Database session
            post_id: Post ID to retrieve content for
        Returns:
            Dictionary with text variations and media content
        """
        text_variations = self.post_service.get_text_variations(db, post_id)
        media_contents = self.post_service.get_media_contents(db, post_id)
        
        return {
            "text_variations": text_variations,
            "media_contents": media_contents
        }

    async def _extract_file_from_sibling_container(
        self,
        container_id: str,
        file_path: str
    ) -> Optional[str]:
        """
        Extract a file from the sibling container.
        
        Args:
            container_id: Docker container ID
            file_path: Path to file inside container
        
        Returns:
            File contents as string or None if failed
        """
        try:
            logger.info(f"Extracting file {file_path} from container {container_id}")
            
            # Use docker cp to copy file from container
            result = subprocess.run(
                ["sudo", "docker", "cp", f"{container_id}:{file_path}", "-"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                content = result.stdout
                logger.info(f"Successfully extracted {len(content)} characters from container")
                return content
            else:
                logger.error(f"Failed to extract file: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout extracting file from container {container_id}")
            return None
        except Exception as e:
            logger.error(f"Error extracting file from container: {e}", exc_info=True)
            return None

    def _copy_file_to_sibling_container(
        self,
        container_id: str,
        src_path: Path,
        dest_path: str
    ) -> bool:
        """Copy a local file into the sibling container."""
        try:
            logger.info(f"Copying {src_path} to container {container_id}:{dest_path}")
            result = subprocess.run(
                ["sudo", "docker", "cp", str(src_path), f"{container_id}:{dest_path}"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("Successfully copied prompt file to sibling container")
                return True

            logger.error(f"Failed to copy prompt file: {result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout copying file into container {container_id}")
            return False
        except Exception as e:
            logger.error(f"Error copying file into container: {e}", exc_info=True)
            return False
    
    async def _extract_from_url(self, url: str) -> Optional[str]:
        """
        Extract text content from a URL.
        
        Args:
            url: URL to extract from
        
        Returns:
            Extracted text or None if failed
        """
        try:
            # Validate URL loads
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            # Parse HTML and extract text
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_text = '\n'.join(lines)
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error extracting from URL {url}: {e}")
            return None
   
    async def _update_post_error(self, db: DBSession, post_id: str, error: str):
        """Update post with error status."""
        self.post_service.update_post_status(
            db, post_id, PostStatus.FAILED,
            error_message=error
        )
    
    async def _send_progress(
        self,
        callback: Optional[Callable],
        step: str,
        message: str,
        **kwargs
    ):
        """Send progress update via callback."""
        if callback:
            try:
                full_message = get_step_description(step, **kwargs) if kwargs else message
                await callback(step, full_message)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
