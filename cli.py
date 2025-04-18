import asyncio
import argparse
import sys
from pathlib import Path # Import Path
import core # Import core directly
import os # Needed for checking prompt file existence

# Define the path to the prompts directory relative to this script's location
# Assuming cli.py is in the root and prompts/ is also in the root.
PROMPTS_DIR = Path(__file__).parent / "prompts" # Use pathlib for robustness

def main():
    parser = argparse.ArgumentParser(
        description="Get image from clipboard, send to OpenAI Vision, put text back to clipboard.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Show defaults in help
    )
    # Prompt selection
    parser.add_argument(
        '-p', '--prompt',
        type=str,
        default='default',
        metavar='NAME',
        help='Prompt file name (without .txt) from "prompts/" directory.'
    )
    # OpenAI Configuration Arguments
    parser.add_argument(
        '--api-key',
        type=str,
        default=os.getenv("OPENAI_API_KEY"), # Default to env var
        metavar='KEY',
        help='OpenAI API key. Overrides OPENAI_API_KEY environment variable.'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), # Default to env var or hardcoded default
        metavar='MODEL_ID',
        help='OpenAI model ID. Overrides OPENAI_MODEL environment variable.'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        default=os.getenv("OPENAI_BASE_URL"), # Default to env var
        metavar='URL',
        help='Custom OpenAI base URL. Overrides OPENAI_BASE_URL environment variable.'
    )

    args = parser.parse_args()

    # --- Validate API Key ---
    if not args.api_key:
         print("❌ Error: OpenAI API key not provided.", file=sys.stderr)
         print("   Provide it via the --api-key argument or set the OPENAI_API_KEY environment variable.", file=sys.stderr)
         sys.exit(1)
    prompt_name = args.prompt

    # --- Execution Logic ---
    # Validate the prompt name
    final_prompt_file = PROMPTS_DIR / f"{prompt_name}.txt"
    if not final_prompt_file.is_file():
        print(f"❌ Error: Selected prompt file '{prompt_name}.txt' not found in '{PROMPTS_DIR}'.", file=sys.stderr)
        # Suggest available prompts
        available_prompts = [f.stem for f in PROMPTS_DIR.glob('*.txt')]
        if available_prompts:
             print(f"   Available prompts: {', '.join(available_prompts)}", file=sys.stderr)
        else:
             print(f"   No prompt files found in '{PROMPTS_DIR}'.", file=sys.stderr)
        sys.exit(1)

    # Run the OCR process once immediately using the specified prompt
    print(f"🚀 Starting ClipGPT-OCR using prompt: '{prompt_name}'...")
    success = asyncio.run(core.run_ocr_process(prompt_name=prompt_name))
    if not success:
        # Error messages are printed within core functions
        sys.exit(1) # Exit with error code if process failed
    else:
        print("✨ Process finished.")

if __name__ == "__main__":
    main()