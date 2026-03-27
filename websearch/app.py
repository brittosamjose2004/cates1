import os
import asyncio
import time
from typing import Optional
from datetime import datetime
import httpx
import trafilatura
import gradio as gr
from dateutil import parser as dateparser
from limits import parse
from limits.aio.storage import MemoryStorage
from limits.aio.strategies import MovingWindowRateLimiter
from analytics import record_request, last_n_days_df, last_n_days_avg_time_df

# Configuration
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_SEARCH_ENDPOINT = "https://google.serper.dev/search"
SERPER_NEWS_ENDPOINT = "https://google.serper.dev/news"
HEADERS = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

# Rate limiting
storage = MemoryStorage()
limiter = MovingWindowRateLimiter(storage)
rate_limit = parse("360/hour")


async def search_web(
    query: str, search_type: str = "search", num_results: Optional[int] = 4
) -> str:
    """
    Search the web for information or fresh news, returning extracted content.

    This tool can perform two types of searches:
    - "search" (default): General web search for diverse, relevant content from various sources
    - "news": Specifically searches for fresh news articles and breaking stories

    Use "news" mode when looking for:
    - Breaking news or very recent events
    - Time-sensitive information
    - Current affairs and latest developments
    - Today's/this week's happenings

    Use "search" mode (default) for:
    - General information and research
    - Technical documentation or guides
    - Historical information
    - Diverse perspectives from various sources

    Args:
        query (str): The search query. This is REQUIRED. Examples: "apple inc earnings",
                    "climate change 2024", "AI developments"
        search_type (str): Type of search. This is OPTIONAL. Default is "search".
                          Options: "search" (general web search) or "news" (fresh news articles).
                          Use "news" for time-sensitive, breaking news content.
        num_results (int): Number of results to fetch. This is OPTIONAL. Default is 4.
                          Range: 1-20. More results = more context but longer response time.

    Returns:
        str: Formatted text containing extracted content with metadata (title,
             source, date, URL, and main text) for each result, separated by dividers.
             Returns error message if API key is missing or search fails.

    Examples:
        - search_web("OpenAI GPT-5", "news") - Get 5 fresh news articles about OpenAI
        - search_web("python tutorial", "search") - Get 4 general results about Python (default count)
        - search_web("stock market today", "news", 10) - Get 10 news articles about today's market
        - search_web("machine learning basics") - Get 4 general search results (all defaults)
    """
    start_time = time.time()

    if not SERPER_API_KEY:
        await record_request(None, num_results)  # Record even failed requests
        return "Error: SERPER_API_KEY environment variable is not set. Please set it to use this tool."

    # Validate and constrain num_results
    if num_results is None:
        num_results = 4
    num_results = max(1, min(30, num_results))

    # Validate search_type
    if search_type not in ["search", "news"]:
        search_type = "search"

    try:
        # Check rate limit
        if not await limiter.hit(rate_limit, "global"):
            print(f"[{datetime.now().isoformat()}] Rate limit exceeded")
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return "Error: Rate limit exceeded. Please try again later (limit: 500 requests per hour)."

        # Select endpoint based on search type
        endpoint = (
            SERPER_NEWS_ENDPOINT if search_type == "news" else SERPER_SEARCH_ENDPOINT
        )

        # Prepare payload
        payload = {"q": query, "num": num_results}
        if search_type == "news":
            payload["type"] = "news"
            payload["page"] = 1

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(endpoint, headers=HEADERS, json=payload)

        if resp.status_code != 200:
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return f"Error: Search API returned status {resp.status_code}. Please check your API key and try again."

        # Extract results based on search type
        if search_type == "news":
            results = resp.json().get("news", [])
        else:
            results = resp.json().get("organic", [])

        if not results:
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return f"No {search_type} results found for query: '{query}'. Try a different search term or search type."

        # Fetch HTML content concurrently
        urls = [r["link"] for r in results]
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            tasks = [client.get(u) for u in urls]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Extract and format content
        chunks = []
        successful_extractions = 0

        for meta, response in zip(results, responses):
            if isinstance(response, Exception):
                continue

            # Extract main text content
            body = trafilatura.extract(
                response.text, include_formatting=False, include_comments=False
            )

            if not body:
                continue

            successful_extractions += 1
            print(
                f"[{datetime.now().isoformat()}] Successfully extracted content from {meta['link']}"
            )

            # Format the chunk based on search type
            if search_type == "news":
                # News results have date and source
                try:
                    date_str = meta.get("date", "")
                    if date_str:
                        date_iso = dateparser.parse(date_str, fuzzy=True).strftime(
                            "%Y-%m-%d"
                        )
                    else:
                        date_iso = "Unknown"
                except Exception:
                    date_iso = "Unknown"

                chunk = (
                    f"## {meta['title']}\n"
                    f"**Source:** {meta.get('source', 'Unknown')}   "
                    f"**Date:** {date_iso}\n"
                    f"**URL:** {meta['link']}\n\n"
                    f"{body.strip()}\n"
                )
            else:
                # Search results don't have date/source but have domain
                domain = meta["link"].split("/")[2].replace("www.", "")

                chunk = (
                    f"## {meta['title']}\n"
                    f"**Domain:** {domain}\n"
                    f"**URL:** {meta['link']}\n\n"
                    f"{body.strip()}\n"
                )

            chunks.append(chunk)

        if not chunks:
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return f"Found {len(results)} {search_type} results for '{query}', but couldn't extract readable content from any of them. The websites might be blocking automated access."

        result = "\n---\n".join(chunks)
        summary = f"Successfully extracted content from {successful_extractions} out of {len(results)} {search_type} results for query: '{query}'\n\n---\n\n"

        print(
            f"[{datetime.now().isoformat()}] Extraction complete: {successful_extractions}/{len(results)} successful for query '{query}'"
        )

        # Record successful request with duration
        duration = time.time() - start_time
        await record_request(duration, num_results)

        return summary + result

    except Exception as e:
        # Record failed request with duration
        duration = time.time() - start_time
        return f"Error occurred while searching: {str(e)}. Please try again or check your query."


# Create Gradio interface
with gr.Blocks(title="Web Search MCP Server") as demo:
    gr.HTML(
        """
        <div style="background-color: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 12px; margin-bottom: 16px; text-align: center;">
            <p style="color: rgb(59, 130, 246); margin: 0; font-size: 14px; font-weight: 500;">
                🤝 Community resource — please use responsibly to keep this service available for everyone
            </p>
        </div>
        """
    )

    gr.Markdown("# 🔍 Web Search MCP Server")

    with gr.Tabs():
        with gr.Tab("App"):
            gr.Markdown(
                """
                This MCP server provides web search capabilities to LLMs. It can perform general web searches
                or specifically search for fresh news articles, extracting the main content from results.
                
                **⚡ Speed-Focused:** Optimized to complete the entire search process - from query to 
                fully extracted web content - in under 2 seconds. Check out the Analytics tab 
                to see real-time performance metrics.
                
                **Search Types:**
                - **General Search**: Diverse results from various sources (blogs, docs, articles, etc.)
                - **News Search**: Fresh news articles and breaking stories from news sources
                
                **Note:** This interface is primarily designed for MCP tool usage by LLMs, but you can 
                also test it manually below.
                """
            )

            gr.HTML(
                """
                <div style="margin-bottom: 24px;">
                    <a href="https://huggingface.co/spaces/victor/websearch?view=api">
                        <img src="https://huggingface.co/datasets/huggingface/badges/resolve/main/use-with-mcp-lg-dark.svg" 
                             alt="Use with MCP" 
                             style="height: 36px;">
                    </a>
                </div>
                """,
                padding=0,
            )

            with gr.Row():
                with gr.Column(scale=3):
                    query_input = gr.Textbox(
                        label="Search Query",
                        placeholder='e.g. "OpenAI news", "climate change 2024", "AI developments"',
                        info="Required: Enter your search query",
                    )
                with gr.Column(scale=1):
                    search_type_input = gr.Radio(
                        choices=["search", "news"],
                        value="search",
                        label="Search Type",
                        info="Choose search type",
                    )

            with gr.Row():
                num_results_input = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=4,
                    step=1,
                    label="Number of Results",
                    info="Optional: How many results to fetch (default: 4)",
                )

            search_button = gr.Button("Search", variant="primary")

            output = gr.Textbox(
                label="Extracted Content",
                lines=25,
                max_lines=50,
                info="The extracted article content will appear here",
            )

            # Add examples
            gr.Examples(
                examples=[
                    ["OpenAI GPT-5 latest developments", "news", 5],
                    ["React hooks useState", "search", 4],
                    ["Tesla stock price today", "news", 6],
                    ["Apple Vision Pro reviews", "search", 4],
                    ["best Italian restaurants NYC", "search", 4],
                ],
                inputs=[query_input, search_type_input, num_results_input],
                outputs=output,
                fn=search_web,
                cache_examples=False,
            )

        with gr.Tab("Analytics"):
            gr.Markdown("## Community Usage Analytics")
            gr.Markdown(
                "Track daily request counts and average response times from all community users."
            )

            with gr.Row():
                with gr.Column():
                    requests_plot = gr.BarPlot(
                        value=last_n_days_df(
                            14
                        ),  # Show only last 14 days for better visibility
                        x="date",
                        y="count",
                        title="Daily Request Count",
                        tooltip=["date", "count"],
                        height=350,
                        x_label_angle=-45,  # Rotate labels to prevent overlap
                        container=False,
                    )

                with gr.Column():
                    avg_time_plot = gr.BarPlot(
                        value=last_n_days_avg_time_df(14),  # Show only last 14 days
                        x="date",
                        y="avg_time",
                        title="Average Request Time (seconds)",
                        tooltip=["date", "avg_time", "request_count"],
                        height=350,
                        x_label_angle=-45,
                        container=False,
                    )

    search_button.click(
        fn=search_web,  # Use search_web directly instead of search_and_log
        inputs=[query_input, search_type_input, num_results_input],
        outputs=output,
        api_name=False,  # Hide this endpoint from API & MCP
    )

    # Load fresh analytics data when the page loads or Analytics tab is clicked
    demo.load(
        fn=lambda: (last_n_days_df(14), last_n_days_avg_time_df(14)),
        outputs=[requests_plot, avg_time_plot],
        api_name=False,
    )

    # Expose search_web as the only MCP tool
    gr.api(search_web, api_name="search_web")


if __name__ == "__main__":
    # Launch with MCP server enabled
    # The MCP endpoint will be available at: http://localhost:7860/gradio_api/mcp/sse
    demo.launch(mcp_server=True, show_api=True)
