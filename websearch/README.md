---
title: Web Search MCP
emoji: 🔎
colorFrom: red
colorTo: green
sdk: gradio
sdk_version: 5.36.2
app_file: app.py
pinned: false
short_description: Search and extract web content for LLM ingestion
thumbnail: >-
  https://cdn-uploads.huggingface.co/production/uploads/5f17f0a0925b9863e28ad517/tfYtTMw9FgiWdyyIYz6A6.png
---

# Web Search MCP Server

A Model Context Protocol (MCP) server that provides web search capabilities to LLMs, allowing them to fetch and extract content from web pages and news articles.

## Features

- **Dual search modes**: 
  - **General Search**: Get diverse results from blogs, documentation, articles, and more
  - **News Search**: Find fresh news articles and breaking stories from news sources
- **Real-time web search**: Search for any topic with up-to-date results
- **Content extraction**: Automatically extracts main article content, removing ads and boilerplate
- **Rate limiting**: Built-in rate limiting (200 requests/hour) to prevent API abuse
- **Structured output**: Returns formatted content with metadata (title, source, date, URL)
- **Flexible results**: Control the number of results (1-20)

## Prerequisites

1. **Serper API Key**: Sign up at [serper.dev](https://serper.dev) to get your API key
2. **Python 3.8+**: Ensure you have Python installed
3. **MCP-compatible LLM client**: Such as Claude Desktop, Cursor, or any MCP-enabled application

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Or install manually:
   ```bash
   pip install "gradio[mcp]" httpx trafilatura python-dateutil limits
   ```

3. Set your Serper API key:
   ```bash
   export SERPER_API_KEY="your-api-key-here"
   ```

## Usage

### Starting the MCP Server

```bash
python app_mcp.py
```

The server will start on `http://localhost:7860` with the MCP endpoint at:
```
http://localhost:7860/gradio_api/mcp/sse
```

### Connecting to LLM Clients

#### Claude Desktop
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "web-search": {
      "command": "python",
      "args": ["/path/to/app_mcp.py"],
      "env": {
        "SERPER_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Direct URL Connection
For clients that support URL-based MCP servers:
1. Start the server: `python app_mcp.py`
2. Connect to: `http://localhost:7860/gradio_api/mcp/sse`

## Tool Documentation

### `search_web` Function

**Purpose**: Search the web for information or fresh news and extract content.

**Parameters**:
- `query` (str, **REQUIRED**): The search query
  - Examples: "OpenAI news", "climate change 2024", "python tutorial"
  
- `num_results` (int, **OPTIONAL**): Number of results to fetch
  - Default: 4
  - Range: 1-20
  - More results provide more context but take longer

- `search_type` (str, **OPTIONAL**): Type of search to perform
  - Default: "search" (general web search)
  - Options: "search" or "news"
  - Use "news" for fresh, time-sensitive news articles
  - Use "search" for general information, documentation, tutorials

**Returns**: Formatted text containing:
- Summary of extraction results
- For each article:
  - Title
  - Source and date
  - URL
  - Extracted main content

**When to use each search type**:
- **Use "news" mode for**:
  - Breaking news or very recent events
  - Time-sensitive information ("today", "this week")
  - Current affairs and latest developments
  - Press releases and announcements

- **Use "search" mode for**:
  - General information and research
  - Technical documentation or tutorials
  - Historical information
  - Diverse perspectives from various sources
  - How-to guides and explanations

**Example Usage in LLM**:
```
# News mode examples
"Search for breaking news about OpenAI" -> uses news mode
"Find today's stock market updates" -> uses news mode
"Get latest climate change developments" -> uses news mode

# Search mode examples (default)
"Search for Python programming tutorials" -> uses search mode
"Find information about machine learning algorithms" -> uses search mode
"Research historical data about climate change" -> uses search mode
```

## Error Handling

The tool handles various error scenarios:
- Missing API key: Clear error message with setup instructions
- Rate limiting: Informs when limit is exceeded
- Failed extractions: Reports which articles couldn't be extracted
- Network errors: Graceful error messages

## Testing

You can test the server manually:
1. Open `http://localhost:7860` in your browser
2. Enter a search query
3. Adjust the number of results
4. Click "Search" to see the extracted content

## Tips for LLM Usage

1. **Choose the right search type**: Use "news" for fresh, breaking news; use "search" for general information
2. **Be specific with queries**: More specific queries yield better results
3. **Adjust result count**: Use fewer results for quick searches, more for comprehensive research
4. **Check dates**: The tool shows article dates for temporal context
5. **Follow up**: Use the extracted content to ask follow-up questions

## Limitations

- Rate limited to 200 requests per hour
- Extraction quality depends on website structure
- Some websites may block automated access
- News mode focuses on recent articles from news sources
- Search mode provides diverse results but may include older content

## Troubleshooting

1. **"SERPER_API_KEY is not set"**: Ensure the environment variable is exported
2. **Rate limit errors**: Wait before making more requests
3. **No content extracted**: Some websites block scrapers; try different queries
4. **Connection errors**: Check your internet connection and firewall settings