# clipocr

A simple CLI utility to grab an image from the clipboard, send it to OpenAI Vision API (GPT-4o-mini by default) for text extraction and rewriting, and put the resulting text back into the clipboard.

## Features

*   **Clipboard Integration:** Reads images directly from the clipboard (`Ctrl+C` / `Cmd+C` on an image or screenshot).
*   **OpenAI Vision:** Uses the powerful vision capabilities of OpenAI's models (configurable via `OPENAI_MODEL` environment variable).
*   **Text Rewriting:** Leverages a customizable system prompt (`prompts/default.txt`) to instruct the AI on how to format the extracted text (default: remove line breaks).
*   **Instant Output:** Places the processed text directly back into the clipboard, ready to paste (`Ctrl+V` / `Cmd+V`).
*   **Environment Variable Configuration:** Securely manages your OpenAI API key via a `.env` file (`OPENAI_API_KEY`).
*   **CLI Interface:** Simple command-line execution.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/msuny-c/clipocr.git
    cd clipocr
    ```
2.  **Install dependencies (using Poetry):**

    ```bash
    pip install poetry
    poetry install
    ```
3.  **Set up your API Key & Configuration:**
    *   Rename `.env.example` to `.env`.
    *   Open `.env` and replace `sk-...` with your actual OpenAI API key.


    ```bash
    cp .env.example .env
    # Now edit .env with your key
    ```

### Global Installation (Recommended: pipx)

[pipx](https://github.com/pypa/pipx) is a tool to install and run Python applications in isolated environments. This is the recommended way to install `clipocr` globally.

1.  **Install pipx:** Follow the official [pipx installation guide](https://pipx.pypa.io/stable/installation/). Usually, it's something like:

    ```bash
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    ```
    *(Restart your terminal after running `ensurepath`)*

2.  **Install clipocr using pipx:**
    *   **From Git:**

        ```bash
        pipx install git+https://github.com/msuny-c/clipocr.git
        ```
    *   **From local source:**

        ```bash
        # Run from the project's root directory
        pipx install .
        ```

3.  **Configuration for Global Install:**
    *   `pipx` installs the script, but you still need to provide the `OPENAI_API_KEY`. Since the `.env` file is usually project-specific, you have a few options:
        *   **Set Environment Variable:** Set the `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`, `OPENAI_BASE_URL`) globally in your system's environment (e.g., in `.zshrc`, `.bashrc`, `.profile`, or system settings). This is the most common method for globally installed tools.
        *   **Place `.env` in Home Directory:** The script *might* find a `.env` file if placed in your home directory (`~/.env`), depending on how `python-dotenv` searches. (Note: This behavior isn't explicitly guaranteed by the current code, which uses default `load_dotenv()` behavior).
        *   **Place `.env` in Working Directory:** If you always run `clipocr` from a specific directory, you could place a `.env` file there.

### Global Installation (Alternative: Standalone Executable)

You can build a standalone executable using PyInstaller (requires Python < 3.13 for the current PyInstaller version).

1.  **Install development dependencies:**

    ```bash
    poetry install --with dev
    ```
2.  **Build the executable:**

    ```bash
    make build-exe
    ```
3.  **Copy the executable:** Find the `clipocr` (or `clipocr.exe`) file inside the `dist/` directory. Copy this file to a location included in your system's `PATH` environment variable (e.g., `/usr/local/bin` on Linux/macOS, or a custom directory you've added to PATH on Windows).
4.  **Configuration:** Similar to the `pipx` method, you'll need to configure the `OPENAI_API_KEY` using global environment variables, as the executable won't automatically find a project-specific `.env` file. The `prompts/` directory is bundled *inside* the executable by the `make build-exe` command, so custom prompts should still work.

## Usage

1.  Copy an image (or take a screenshot) to your clipboard.
2.  Run the script from your terminal:

    ```bash
    poetry run clipocr
    ```
    Or, if you installed it globally or are using a virtual environment activated differently:

    ```bash
    clipocr
    ```

## Configuration

*   **API Key:** (Required) Set `OPENAI_API_KEY` in your `.env` file.
*   **Model:** (Optional) Set `OPENAI_MODEL` in your `.env` file (e.g., `OPENAI_MODEL="gpt-4-vision-preview"`). Defaults to `gpt-4o-mini` if not set.
*   **Base URL:** (Optional) Set `OPENAI_BASE_URL` in your `.env` file if you need to use a custom OpenAI-compatible API endpoint.
*   **System Prompts:** (Optional) Modify or add prompt files (simple `.txt` files) in the `prompts/` directory. The name of the file (without `.txt`) is used to select the prompt via the `--prompt` flag. Default is `prompts/default.txt`.

## Command-Line Arguments

*   `--prompt PROMPT_NAME` or `-p PROMPT_NAME`: Specify which prompt file from the `prompts/` directory to use (e.g., `-p markdown`). Defaults to `default`.
## Development

*   **Install Dev Dependencies:** Make sure you have installed development dependencies.

    ```bash
    poetry install --with dev
    ```
*   **Linting:** Check code style using `ruff`.

    ```bash
    make lint
    # Or: poetry run ruff check .
    ```
*   **Building Executable:** Create a standalone executable using `PyInstaller`. The executable will be placed in the `dist/` directory.

    ```bash
    make build-exe
    # Or: poetry run pyinstaller --onefile --name clipocr --add-data "prompts:prompts" cli.py
    ```

## TODO

*   Write more comprehensive tests, especially for `cli.py` and `hotkey.py` (mocking `argparse`, `keyboard`, etc.).
*   Set up CI/CD (e.g., GitHub Actions) for automated linting and testing.
*   Consider adding code coverage reporting (e.g., using `pytest-cov`).
*   Create build packages for other platforms (e.g., macOS App, Linux .deb/AppImage).