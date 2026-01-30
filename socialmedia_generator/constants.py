"""
Application-wide constants for Social Media Post Generator.

Defines paths, file names, and configuration constants used across services.
"""

from pathlib import Path


class FileConstants:
    """File path constants for post generation workflow."""
    
    # Context file saved during source extraction
    CONTEXT_FILE_NAME = "context.txt"
    CONTEXT_FILE_PATH = f"/tmp/{CONTEXT_FILE_NAME}"

    # Prompt file saved before sampling loop
    TEXT_PROMPT_FILE_NAME = "prompt.txt"
    TEXT_PROMPT_FILE_PATH = f"/tmp/{TEXT_PROMPT_FILE_NAME}"
    
    # Image generation prompt file
    IMAGE_PROMPT_FILE_NAME = "image_prompt.txt"
    IMAGE_PROMPT_FILE_PATH = f"/tmp/{IMAGE_PROMPT_FILE_NAME}"

    # Google login helper script
    GOOGLE_LOGIN_SCRIPT_NAME = "google_login.py"
    GOOGLE_LOGIN_SCRIPT_PATH = f"/tmp/{GOOGLE_LOGIN_SCRIPT_NAME}"
    
    # Google search result file
    GOOGLE_SEARCH_RESULT_FILE_NAME = "google_search_result.txt"
    GOOGLE_SEARCH_RESULT_PATH = f"/tmp/{GOOGLE_SEARCH_RESULT_FILE_NAME}"
    
    # Generated images directory
    GENERATED_IMAGES_DIR = "/tmp/generated_images"
    
    # Generated content output
    TEXT_VARIATIONS_FILE_NAME = "text_variations.json"
    TEXT_VARIATIONS_PATH = f"/tmp/{TEXT_VARIATIONS_FILE_NAME}"
    
    IMAGE_METADATA_FILE_NAME = "image_metadata.json"
    IMAGE_METADATA_PATH = f"/tmp/{IMAGE_METADATA_FILE_NAME}"


class ContentTypeConstants:
    """Constants for content type mappings."""
    
    # Content type to string mapping
    CONTENT_TYPE_MAP = {
        "LongForm": "The generated content should be a long form post suitable for blogs or articles.",
        "ShortForm": "The generated content should be a short form post suitable for social media or quick reads."
    }


class AgentConstants:
    """Constants for agent execution configuration."""
    
    # Default max iterations for sampling loop
    DEFAULT_MAX_ITERATIONS = 10
    
    # Default thinking budget for Claude
    DEFAULT_THINKING_BUDGET = 10000
    
    # Tool versions mapping
    TOOL_VERSION_OPUS_45 = "computer_use_20251124"
    TOOL_VERSION_SONNET_45 = "computer_use_20250124"
    TOOL_VERSION_OPUS_4 = "computer_use_20250429"
    TOOL_VERSION_DEFAULT = "computer_use_20250124"
