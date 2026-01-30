"""
Predefined prompts for Google Gemini interactions.

Contains templates for text generation, image generation, and other tasks.
"""

# ============================================================================
# Web Search Prompts
# ============================================================================

GOOGLE_SEARCH_INSTRUCTION = """Use the computer to search Google for information related to: "{search_query}"

STEPS:
1. Open a web browser
2. Navigate to google.com or use the search bar if available
3. Enter the search query: {search_query}
4. Press Enter to search
5. Review the top search results
6. Click on the FIRST result that appears to have valid text content (typically a news article, blog, or informational page)
7. Wait for the page to load completely
8. Extract ALL visible text content from the page
9. Save the extracted text to a file named: "google_search_result.txt" in the /tmp directory

IMPORTANT:
- Only extract the FIRST result with valid content
- Do NOT click on images, videos, or ads
- Do NOT go deeper into nested pages
- MUST save the extracted content to /tmp/google_search_result.txt
- The file must contain the full text content from the webpage
"""

# ============================================================================
# Text Generation Prompts
# ============================================================================

TEXT_GENERATION_PROMPT_TEMPLATE = """You are a professional social media content creator. Generate {num_variations} different variations of a social media post based on the following context.

CONTEXT:
{context}

LANGUAGE AND TONE REQUIREMENTS:
{language_tone}

INSTRUCTIONS:
1. Create {num_variations} unique variations of the post text
2. Each variation should have a different style while maintaining the same core message
3. Include relevant hashtags where appropriate
4. Keep each post engaging and suitable for social media
5. For EACH variation, also provide image generation prompts/tags that would create compelling visual content related to that specific variation

IMPORTANT - OUTPUT FORMAT:
You MUST respond with ONLY a valid JSON object in this exact format (no code blocks, no markdown, no extra text):

{{
  "variations": [
    {{
      "variation_number": 1,
      "text_content": "The actual post text for variation 1",
      "image_prompts": ["prompt 1 for variation 1", "prompt 2 for variation 1", "prompt 3 for variation 1"]
    }},
    {{
      "variation_number": 2,
      "text_content": "The actual post text for variation 2",
      "image_prompts": ["prompt 1 for variation 2", "prompt 2 for variation 2", "prompt 3 for variation 2"]
    }}
  ]
}}

Generate {num_variations} variations now.
"""

# ============================================================================
# Text and Image Text Prompt Generation Prompts
# ============================================================================

TEXT_AND_IMAGE_GENERATION_PROMPT_TEMPLATE = """You are a professional social media content creator. Generate {num_variations} different variations of a social media post based on the following context.

CONTEXT:
{context}

LANGUAGE AND TONE REQUIREMENTS:
{language_tone}

TYPE OF CONTENT TO GENERATE:
{content_type}

INSTRUCTIONS:
1. Create {num_variations} unique variations of the post text
2. Each variation should have a different style while maintaining the same core message
3. Include relevant hashtags where appropriate
4. Keep each post engaging and suitable for social media
5. Also provide relevant {image_num_variations} image generation prompts/tags that would create compelling visual content related to that specific variation

IMPORTANT - OUTPUT FORMAT:
Do not having trailing commas or syntax errors in the JSON.
You MUST respond with ONLY a valid JSON object in this exact format (no code blocks, no markdown, no extra text):

IMAGE PROMPT RULES:
- The image prompts should be general enough to apply to the overall post content, not tied to specific text variations.
- Each image prompt should inspire a unique visual representation of the post's theme.
- Avoid overly specific details that limit creative interpretation.
- Do not generate prompts that any way indicate charts, graphs, or infographics.

An Example Response if 2 unique variations of the post text and 3 image generation prompts are requested:
{{
  "variations": [
    {{
      "variation_number": 1,
      "text_content": "The actual post text for variation 1"
    }},
    {{
      "variation_number": 2,
      "text_content": "The actual post text for variation 2"
    }}
  ],
  "image_prompts":[
    "prompt 1 for overall post",
    "prompt 2 for overall post",
    "prompt 3 for overall post"
  ]
}}

Generate ONLY {num_variations} text variations and ONLY {image_num_variations} image prompts now.
"""


# ============================================================================
# Image Generation Prompts
# ============================================================================

IMAGE_GENERATION_PROMPT_TEMPLATE = """Generate an image based on the following description:

POST CONTEXT:
{post_text}

IMAGE GENERATION PROMPT:
{image_prompt}

STYLE REQUIREMENTS:
- Professional and suitable for social media
- High quality and visually appealing
- Relevant to the post content
- Eye-catching and engaging

Create the image now.
"""


# ============================================================================
# Context Extraction Prompts
# ============================================================================

CONTEXT_EXTRACTION_PROMPT = """Extract and summarize the main content from the provided text. Focus on:
1. Key facts and information
2. Main themes and topics
3. Important details that would be relevant for social media content

Provide a clear, concise summary that captures the essence of the content.

TEXT TO ANALYZE:
{text_content}
"""


# ============================================================================
# Google Gemini Navigation Prompts
# ============================================================================

GEMINI_LOGIN_INSTRUCTION = """Navigate to https://gemini.google.com and log in if not already logged in.

Steps:
1. Go to the Gemini website
2. If you see a login page, click on the sign-in button
3. Wait for login to complete
4. Verify you're on the main Gemini chat interface
"""


GEMINI_LOGIN_WITH_SCRIPT_INSTRUCTION = """Open https://gemini.google.com and log in using the preloaded helper script inside the container.

Steps:
1. Navigate to https://gemini.google.com in the browser.
2. Click on Login, If a Google sign-in page is shown, click the email/username field to focus it.
3. Run the helper script to type the credentials automatically:
    python3 /tmp/google_login.py
    - The script reads GOOGLE_EMAIL and GOOGLE_PASSWORD from the environment.
    - It types the email, presses Enter, waits briefly, types the password, then presses Enter.
4. Wait for the login to finish and confirm you're on the Gemini chat interface.
5. If login fails, rerun the script after ensuring the correct field is focused.

IMPORTANT INSTRUCTIONS:
- Ensure the gemini website is left open and active in the browser.
- DO NOT verify if the environment variables are available or if script exists; they are preloaded.
"""


GEMINI_NEW_CHAT_INSTRUCTION = """Start a new chat in Google Gemini.

Steps:
1. Look for the "New chat" or "+" button (usually in the sidebar or top of the page)
2. Click it to start a fresh conversation
3. Wait for the new chat interface to load
"""


GEMINI_UPLOAD_FILE_INSTRUCTION = """Upload the file located at: {file_path}

Steps:
1. Look for the attachment/upload button (usually a paperclip icon or "+" button near the text input)
2. Click the upload button
3. Navigate to and select the file: {file_path}
4. Wait for the file to upload successfully
5. Verify the file appears in the chat
"""


GEMINI_SEND_PROMPT_INSTRUCTION = """Type and send the following prompt to Gemini:

{prompt}

Steps:
1. Click in the text input area
2. Type or paste the exact prompt above
3. Press Enter or click the Send button
4. Wait for Gemini to generate the response
"""


GEMINI_EXTRACT_RESPONSE_INSTRUCTION = """Extract the text response from Gemini's latest message.

Steps:
1. Wait for Gemini to finish generating the response (look for the "generating" indicator to disappear)
2. Locate the latest response message from Gemini
3. Copy the entire text content (exclude any code blocks if they're just formatting)
4. Save the response for processing
"""


GEMINI_UPLOAD_PROMPT_AND_GENERATE_INSTRUCTION = """Navigate to https://gemini.google.com, upload the prompt file, and generate content based on it.

Steps:
1. Navigate to https://gemini.google.com in the browser , if already opened , then skip this step
2. Ensure you are logged in and on the main Gemini chat interface
3. Start a new chat (click "New chat" icon or "+" button)
4. Locate the attachment/upload button (usually a paperclip icon or "+" button near the text input area)
5. Click the upload button
6. Navigate to -> Other locations -> tmp folder and then select the file: /tmp/prompt.txt
7. Wait for the file to upload successfully and appear in the chat
8. In the text input area, type the following message:
   "Please refer to the prompt/instructions in the uploaded file and generate the content as requested."
9. Press Enter or click the Send button
10. Wait for Gemini to read the file and generate the response
11. Wait for the generation to complete (look for the "generating" indicator to disappear)
13. Scroll to the bottom below the latest response
12. If the generated content is text-based, follow these steps to save it:
13. Locate the response buttons below Gemini's message (REDO, COPY, THREE DOT MENU)
14. Click the COPY button to copy the generated text to clipboard
15. Save the copied content to /tmp/text_variations.json using a Unix command like:
    xclip -o -selection clipboard > /tmp/text_variations.json
    OR
    echo "$(xdotool key --clearmodifiers ctrl+v)" > /tmp/text_variations.json
16. If the generated content is image-based, follow these steps to save it:
17. Locate the images in Gemini's response
18. Right-click each image and select "Save image as..." to save them to /tmp/generated_images/ directory

IMPORTANT:
- Make sure the file /tmp/prompt.txt exists before uploading
- Wait for Gemini to fully process the file before expecting a response
- The generated content should be saved to /tmp/text_variations.json or /tmp/generated_images/ as appropriate
"""


# ============================================================================
# Agent Step Descriptions (for WebSocket updates)
# ============================================================================

STEP_DESCRIPTIONS = {
    "initializing": "Initializing post generation process...",
    "validating_sources": "Validating data sources...",
    "extracting_context": "Extracting content from source #{source_num}: {source_type}...",
    "saving_context": "Saving extracted context...",
    "opening_gemini": "Opening Google Gemini...",
    "logging_in": "Logging into Google account...",
    "creating_new_chat": "Creating new chat session...",
    "uploading_context": "Uploading context file to Gemini...",
    "generating_text": "Generating text variation #{variation_num}...",
    "extracting_text_response": "Extracting generated text content...",
    "saving_text_variations": "Saving text variations to database...",
    "generating_image": "Generating image variation #{variation_num} using prompt: {prompt}...",
    "saving_image": "Saving generated image...",
    "finalizing": "Finalizing post generation...",
    "completed": "Post generation completed successfully! {content}",
    "error": "Error occurred: {error_message}"
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_text_generation_prompt(context: str, language_tone: str, num_variations: int = 3) -> str:
    """
    Generate the text generation prompt with given parameters.
    
    Args:
        context: Combined context from all data sources
        language_tone: Desired language and tone
        num_variations: Number of variations to generate
    
    Returns:
        Formatted prompt string
    """
    return TEXT_GENERATION_PROMPT_TEMPLATE.format(
        context=context,
        language_tone=language_tone,
        num_variations=num_variations
    )


def get_image_generation_prompt(post_text: str, image_prompt: str) -> str:
    """
    Generate the image generation prompt.
    
    Args:
        post_text: The post text for context
        image_prompt: Specific image generation prompt
    
    Returns:
        Formatted prompt string
    """
    return IMAGE_GENERATION_PROMPT_TEMPLATE.format(
        post_text=post_text,
        image_prompt=image_prompt
    )


def get_step_description(step: str, **kwargs) -> str:
    """
    Get a user-friendly description for a processing step.
    
    Args:
        step: Step identifier
        **kwargs: Format parameters for the description
    
    Returns:
        Formatted step description
    """
    template = STEP_DESCRIPTIONS.get(step, f"Processing step: {step}")
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
