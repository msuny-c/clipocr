import base64
import io
import os
import sys
import asyncio
import time # For sleep in retries
from pathlib import Path
import pyperclip
# Import specific exceptions from openai
from openai import (
    OpenAI, AsyncOpenAI, APIError, RateLimitError, BadRequestError, APITimeoutError, APIConnectionError
)
from PIL import ImageGrab
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the path to the prompts directory relative to this file's parent
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_system_prompt(prompt_name: str = "default") -> str:
    """Loads the specified prompt file from the prompts directory."""
    prompt_file = PROMPTS_DIR / f"{prompt_name}.txt"
    if not PROMPTS_DIR.is_dir():
         print(f"❌ Error: Prompts directory not found at '{PROMPTS_DIR}'", file=sys.stderr)
         sys.exit(1)
    try:
        print(f"🔧 Loading prompt: {prompt_file.name}")
        return prompt_file.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"❌ Error: Prompt file '{prompt_file.name}' not found in '{PROMPTS_DIR}'.", file=sys.stderr)
        print(f"   Available prompts: {[f.stem for f in PROMPTS_DIR.glob('*.txt')]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading prompt file '{prompt_file.name}': {e}", file=sys.stderr)
        sys.exit(1)

# Get configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") # Will be None if not set

# Initialize OpenAI client
# Use AsyncOpenAI for the async function
try:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    client_params = {
        "api_key": OPENAI_API_KEY,
    }
    if OPENAI_BASE_URL:
        client_params["base_url"] = OPENAI_BASE_URL
        print(f"🔧 Using custom OpenAI base URL: {OPENAI_BASE_URL}")

    client = AsyncOpenAI(**client_params)
    # Also initialize a sync client for potential future sync needs or checks
    sync_client = OpenAI(**client_params)
    print(f"🤖 Configured to use OpenAI model: {OPENAI_MODEL}")

except (ValueError, Exception) as e:
    print(f"❌ Error initializing OpenAI client: {e}", file=sys.stderr)
    if isinstance(e, ValueError):
         print("   Please set the OPENAI_API_KEY in your environment or .env file.", file=sys.stderr)
    sys.exit(1)


def get_image_from_clipboard() -> bytes | None:
    """Grabs an image from the clipboard."""
    try:
        im = ImageGrab.grabclipboard()
        if im is None:
            return None
        # Check if it's actually an image object (PIL formats)
        if not hasattr(im, 'save'):
             print("📋 Clipboard content is not a recognized image format.", file=sys.stderr)
             return None
        buf = io.BytesIO()
        # Ensure saving as PNG, as specified in the API call format
        im.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        # Optional: Check image size before sending (OpenAI limit is ~20MB, but practically lower for base64)
        # size_mb = len(img_bytes) / (1024 * 1024)
        # if size_mb > 15: # Example threshold, adjust as needed
        #     print(f"⚠️ Warning: Image size ({size_mb:.2f} MB) is large, might exceed API limits.", file=sys.stderr)
        return img_bytes
    except Exception as e:
        # Catch potential errors during clipboard access or image processing
        print(f"❌ Error getting image from clipboard: {e}", file=sys.stderr)
        return None


MAX_RETRIES = 3
INITIAL_BACKOFF = 1 # seconds

async def ocr_and_rewrite(img_bytes: bytes, system_prompt: str) -> str | None:
    """
    Encodes image, sends to OpenAI with retries and specific error handling,
    returns the text response.
    """
    try:
        b64_image = base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        print(f"❌ Error encoding image to Base64: {e}", file=sys.stderr)
        return None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [
            {"type": "text", "text": "Process the text from the image according to the system instructions."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
        ]} # Close content list
    ] # Close messages list

    current_retry = 0
    backoff_time = INITIAL_BACKOFF

    while current_retry <= MAX_RETRIES:
        try:
            print(f"🤖 Sending request to OpenAI model: {OPENAI_MODEL} (Attempt {current_retry + 1}/{MAX_RETRIES + 1})...")
            resp = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                timeout=60, # Increased timeout for potentially larger images/slower responses
            )
            # Basic check for response structure
            if resp.choices and resp.choices[0].message and resp.choices[0].message.content:
                 extracted_text = resp.choices[0].message.content.strip()
                 print("✅ Received response from OpenAI.")
                 return extracted_text
            else:
                 # Handle cases where the response might be empty or structured differently
                 finish_reason = resp.choices[0].finish_reason if resp.choices else "unknown"
                 if finish_reason == "content_filter":
                      print("❌ OpenAI response blocked due to content filter.", file=sys.stderr)
                 elif finish_reason == "length":
                      print("⚠️ OpenAI response truncated due to max_tokens limit.", file=sys.stderr)
                      # Return truncated content if available
                      if resp.choices and resp.choices[0].message and resp.choices[0].message.content is not None:
                           return resp.choices[0].message.content.strip()
                 else:
                      print(f"❌ OpenAI response structure unexpected or empty (Finish reason: {finish_reason}).", file=sys.stderr)
                      print(f"Full response: {resp}", file=sys.stderr)
                 return None # Don't retry on unexpected structure or content filter

        except APITimeoutError as e:
            print(f"⏳ OpenAI API request timed out: {e}", file=sys.stderr)
            # Retryable
        except APIConnectionError as e:
            print(f"🌐 OpenAI API connection error: {e}", file=sys.stderr)
            # Retryable
        except APIError as e:
            # Retry on server errors (5xx), but not client errors (4xx) unless specified
            if e.status_code >= 500:
                print(f"🔧 OpenAI API server error ({e.status_code}): {e}", file=sys.stderr)
                # Retryable
            else:
                print(f"❌ OpenAI API client error ({e.status_code}): {e}", file=sys.stderr)
                if e.code == 'invalid_api_key':
                     print("   🔑 Please check your OPENAI_API_KEY.", file=sys.stderr)
                # Add more specific checks if needed based on e.code or e.body
                return None # Non-retryable client error
        except RateLimitError as e:
            print(f"🚦 OpenAI API rate limit exceeded: {e}", file=sys.stderr)
            # Consider parsing e.response.headers.get("Retry-After") for smarter backoff
            retry_after_str = e.response.headers.get("Retry-After")
            wait_time = backoff_time # Default backoff if header not present/parsable
            if retry_after_str:
                try:
                    wait_time = int(retry_after_str) + 1 # Add a buffer
                    print(f"   Rate limit suggests waiting {wait_time} seconds.")
                except ValueError:
                    pass # Use default backoff if header is not an integer
            backoff_time = wait_time # Use suggested wait time if available
            # Decide whether to retry based on MAX_RETRIES or just give up
            # For simplicity here, we'll retry using the adjusted backoff_time if within MAX_RETRIES
            print(f"   Will attempt retry if within limit ({current_retry + 1} <= {MAX_RETRIES + 1}).")
            # Retryable (with potentially longer backoff)

        except BadRequestError as e:
            print(f"🚫 OpenAI API bad request error: {e}", file=sys.stderr)
            error_body = e.body or {}
            error_code = error_body.get("code", "")
            error_message = error_body.get("message", "")

            if "image_too_large" in error_code or "image_too_large" in error_message:
                 print("   🖼️ The image is too large. Please use a smaller image (max ~20MB, recommended < 10MB).", file=sys.stderr)
            elif error_code == 'invalid_image_url' or "Invalid image" in error_message:
                 print("   🖼️ The image format might be invalid or corrupted.", file=sys.stderr)
            elif error_code == 'invalid_request_error' or "Invalid request" in error_message:
                 print(f"   🤔 Invalid request structure or parameters. Details: {error_message}", file=sys.stderr)
            else:
                 print(f"   Details: Code={error_code}, Message={error_message}", file=sys.stderr)
            return None # Non-retryable
        except Exception as e:
            # Catch any other unexpected exceptions during the API call
            print(f"❌ Unexpected error during OpenAI API call: {type(e).__name__}: {e}", file=sys.stderr)
            return None # Non-retryable

        # --- Retry Logic ---
        current_retry += 1
        if current_retry <= MAX_RETRIES:
            print(f"   Retrying in {backoff_time:.2f} seconds...")
            await asyncio.sleep(backoff_time)
            # Exponential backoff only if not overridden by RateLimitError header
            if not isinstance(e, RateLimitError):
                 backoff_time *= 2
        else:
            print("❌ Max retries reached. Failed to get response from OpenAI.", file=sys.stderr)
            return None

    return None # Should theoretically not be reached


async def run_ocr_process(prompt_name: str = "default"):
    """Main async logic: get image, load prompt, OCR, copy to clipboard."""
    # Load the specified system prompt
    system_prompt = load_system_prompt(prompt_name)

    print("📋 Checking clipboard for image...")
    img_bytes = get_image_from_clipboard()

    if img_bytes is None:
        print("❌ No image found in clipboard.")
        return False # Indicate failure

    print(f"🖼️ Image found, processing with OpenAI using prompt '{prompt_name}'...")
    extracted_text = await ocr_and_rewrite(img_bytes, system_prompt) # Pass the loaded prompt

    if extracted_text is not None:
        try:
            pyperclip.copy(extracted_text)
            print("✅ Text successfully copied to clipboard!")
            return True # Indicate success
        except Exception as e:
            print(f"❌ Error copying text to clipboard: {e}", file=sys.stderr)
            return False # Indicate failure
    else:
        print("❌ Failed to get text from OpenAI.")
        return False # Indicate failure

# Example of how to run the async function if this file were executed directly
# if __name__ == "__main__":
#     # Example: asyncio.run(run_ocr_process(prompt_name="markdown"))
#     asyncio.run(run_ocr_process())