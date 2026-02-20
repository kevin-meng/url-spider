# Plan: Headless Obsidian Web Clipper

## Goal
Develop a Python-based headless CLI tool that converts URLs to Markdown, strictly following the user's existing `obsidian-web-clipper-settings.json` configuration. This allows for automated, background archiving of articles (e.g., from Zhihu) without requiring a visible browser or manual interaction.

## Architecture

### 1. Core Components
- **Settings Loader**: Parses the `obsidian-web-clipper-settings.json` to understand:
  - **Templates**: Different extraction rules for different sites (e.g., Zhihu Answer vs. Column).
  - **Triggers**: Regex/Glob patterns to match URLs to templates.
  - **Properties**: Metadata fields (Title, Author, Date, etc.) defined by CSS selectors.
- **Fetcher (Headless Browser)**:
  - Uses **Playwright** (Python) to load pages.
  - Handles dynamic content (SPA), lazy loading, and basic anti-bot measures.
- **Extractor & Template Engine**:
  - Parses the custom template syntax used in the settings file (e.g., `{{selector:.class}}`, `{{content|markdown}}`).
  - Implements a mini-engine to handle filters like `replace`, `date`, `split`, `join`.
- **Markdown Converter**:
  - Uses `markdownify` or `trafilatura` to convert HTML segments (like the main article body) into clean Markdown.

### 2. Workflow
1. **Input**: User provides a URL.
2. **Match**: Script scans `template_list` in settings to find a template where `triggers` match the URL.
3. **Fetch**: Playwright loads the URL (headless).
4. **Extract**:
   - Loop through `properties` in the template.
   - Execute CSS selectors (e.g., `.RichContent-inner`) to get text or HTML.
   - Apply filters (e.g., convert HTML to Markdown, format dates).
5. **Render**:
   - Fill in the `noteNameFormat` (filename).
   - Fill in the `noteContentFormat` (file content).
   - Construct the Frontmatter (YAML header).
6. **Output**: Save the resulting Markdown file to a specified directory (e.g., `inbox`).

## Technology Stack
- **Language**: Python 3.10+
- **Browser Automation**: `playwright` (Robust, fast, headless).
- **HTML Parsing**: `beautifulsoup4` (Flexible extraction).
- **Markdown Conversion**: `markdownify` (Customizable HTML->MD).
- **Templating**: Custom logic to parse the specific Obsidian-plugin syntax.

## Implementation Steps
1. **Setup**: Initialize Python environment and install dependencies.
2. **Parser Implementation**: Write regex/logic to parse `{{selector:...|filter}}` syntax.
3. **CLI Development**: Create `clipper.py` that accepts a URL.
4. **Testing**: Verify against a Zhihu article using the user's provided settings.

## Future Enhancements
- Docker support for running as a service.
- API endpoint (FastAPI) to trigger clipping via webhook.
