# LangChain Meets MCP: Creating an ArXiv Research Chatbot from Scratch
*A practical approach of leveraging MCP with LangChain to build a user-friendly assistant for navigating and understanding articles.*

## TL;DR
Model Context Protocols (MCPs) are standardized adapters that let AI applications connect to external data sources and tools. We build a research assistant using MCP, LangChain, FastAPI, and Streamlit. The system leverages multiple MCP servers to search scientific papers on ArXiv and parse via docling OCR the content for question answering.

---

**Introduction**  
Large Language Models (LLMs) are everywhere, powering applications from chatbots to complex AI assistants. Yet, behind the scenes, integrating external data and functionalities often involves creating some boilerplate tools, prompts, data, etc repeatedly. This is where the Model Context Protocol (MCP) makes a significant impact even powering AI-assisted software like Cursor or Claude Desktop, leveraging programmatic and customizable use of tools while benefitting from LLM's *reasoning* capabilities.

MCP is designed to bridge the gap between LLMs and real-world data. It acts as a **universal adapter** (everyone seems to dig the analogy of MCP as a "*USB-C port*") for AI applications—providing a standardized and secure way to expose external data and functionality to your models. MCP separates the concerns of providing context from LLM interactions. This means you can build MCP servers that expose:
  
- **Resources:** Data endpoints (similar to GET requests) that load context into your LLM.
- **Tools:** Functional endpoints (like POST requests) that allow your LLM to execute code or trigger side effects.
- **Prompts:** Reusable templates that standardize interactions.

In other words, MCP eliminates the extra work of creating tools, etc for each project, allowing out-of-the-box integration with the outside world (or paid APIs).

In this project, we'll use MCP alongside **LangChain**, **FastAPI**, and **Streamlit** to create a simple yet powerful research assistant. The architecture is composed of three main components:

1. **MCP Servers:**  
   - **ArXiv Server:** Provides the tools necessary for searching and retrieving scientific papers.  
   - **DocLing Server:** Offers document linguistic tools for analyzing text and extracting key insights.

2. **FastAPI Client Server:**  
   Acting as the coordination layer, this server aggregates the functionalities of the MCP servers. It implements the research assistant agent that leverages multiple MCP tools and exposes a unified API for client interactions.

3. **Streamlit UI:**  
   This user-friendly web interface allows users to submit research queries, view search results, and analyze documents seamlessly.

And the result is something like this:  
![search and open article](assets\search_and_open.gif)  
![parse and answer](assets\parse_and_answer.gif)

By leveraging MCP, we could easily expand the capabilities of this research assistant. For instance, we could add more MCP servers to integrate with other search mechanisms or even add a persistent database by connecting to a ChromaDB database via MCP. You either pay for some ready-to-use MCP tool out there or build your own, the choice is yours!

In the next section, we'll dive into a hands-on tutorial where we implement MCP servers with a LangChain ReAct agent.

## Hands-On: Building MCP Servers with LangChain

For the full code and additional details, feel free to check out my GitHub repo: [mcp-demo](https://github.com/raca159/mcp-demo). From there, you just need to clone the repository then run:

```bash
docker-compose up --build
```

And you'll be greeted with a Streamlit UI like this.

![Streamlit UI](assets\streamlit_overview.png)

In this section, we’ll focus on the core components that make our research assistant tick: the MCP servers (which power our ArXiv search and document analysis) and the FastAPI client server that coordinates these services.

### MCP Servers

Our design splits the backend into two dedicated MCP servers:

#### 1. ArXiv Server

The ArXiv server is responsible for querying and retrieving scientific articles from ArXiv. Here’s what it does:
- **Article Model:** Uses a Pydantic model to structure the search results.
- **Search Function:** Leverages the [arxiv](https://pypi.org/project/arxiv/) library to search for research papers based on a query.
- **Tool Exposure:** Exposes the `get_articles` function as an MCP tool (via the `@mcp.tool` decorator) so that it can be invoked by the client server.

Below is a simplified version of the code:

```python
# arxiv_server.py
import arxiv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import asyncio
from typing import Optional

# Initialize MCP server on port 8000
mcp = FastMCP("Research Article Provider", port=8000)

class Article(BaseModel):
    title: str
    summary: str
    published_date: str
    pdf_link: Optional[str]

    @classmethod
    def from_arxiv_result(cls, result: arxiv.Result) -> 'Article':
        pdf_links = [str(i) for i in result.links if '/pdf/' in str(i)]
        pdf_link = pdf_links[0] if pdf_links else None
        return cls(
            title=result.title,
            summary=result.summary,
            published_date=result.published.strftime('%Y-%m-%d'),
            pdf_link=pdf_link
        )
    
    def __str__(self):
        return (f'Title: {self.title}\nDate: {self.published_date}\n'
                f'PDF Url: {self.pdf_link}\n\n' +
                '\n'.join(self.summary.splitlines()[:3]) + '\n[...]')

def get_articles_content(query: str, max_results: int) -> list[Article]:
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    articles = map(lambda x: Article.from_arxiv_result(x), client.results(search))
    articles_with_link = filter(lambda x: x.pdf_link is not None, articles)
    return list(articles_with_link)

@mcp.tool(
    name="search_arxiv",
    description="Get `max_results` articles for a given search query on Arxiv."
)
async def get_articles(query: str, max_results: int) -> str:
    print(f"Searching for '{query}'...")
    articles = get_articles_content(query, max_results)
    print(f"Found {len(articles)} articles.")
    return '\n\n-------\n\n'.join(map(str, articles)).strip()

if __name__ == "__main__":
    asyncio.run(mcp.run_sse_async())
```

Look at how simple it is to expose a tool using MCP! We just create a `FastMCP` entity representing the server (like FastAPI), and then The `@mcp.tool` decorator automatically registers the function with the MCP server, making it accessible to the client-server. The `get_articles` function is the actual logic, searching for articles on ArXiv based on relevance, and returns a formatted string with the results. Here is what it looks like:

![Streamlit serach](assets\streamlit_search.png)

#### 2. DocLing Server

The DocLing server handles the extraction and preview generation of article content from PDFs. Key points include:
- **Document Conversion:** Uses a `DocumentConverter` (from the [docling](https://github.com/docling-project/docling) library) to convert PDF content into Markdown.
- **Text Previewing:** Implements a text splitter (using LangChain’s `RecursiveCharacterTextSplitter` and `tiktoken`) to grab the first chunk of text for quick previews.
- **Exposed Tools:** Provides two tools: one to extract the full text and another to retrieve a preview.

Here’s a version of the DocLing server code:

```python
# docling_server.py
from mcp.server.fastmcp import FastMCP
from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken
import asyncio

# Initialize MCP server on port 8001
mcp = FastMCP("Research Article Extraction Provider", port=8001)

def get_article_content_str(article_url: str):
    converter = DocumentConverter()
    result = converter.convert(article_url)
    return result.document.export_to_markdown()

def first_lines(text: str, chunk_size: int = 1536) -> str:
    encoder = tiktoken.encoding_for_model('gpt-4')
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=0,
        length_function=lambda x: len(encoder.encode(x)),
        is_separator_regex=False,
    )
    return text_splitter.split_text(text)[0]

@mcp.tool(
    name="extract_article_content",
    description="Extracts the full text content from a research article PDF using OCR."
)
async def get_article_content(article_url: str) -> str:
    return get_article_content_str(article_url).strip()

@mcp.tool(
    name="get_article_preview",
    description="Retrieves the first portion of a research article for quick previews."
)
async def get_article_first_lines(article_url: str, chunk_size: int = 1536) -> str:
    articlecontent = get_article_content_str(article_url)
    return first_lines(articlecontent.strip(), chunk_size).strip()

if __name__ == "__main__":
    asyncio.run(mcp.run_sse_async())
```

Similar to the ArXiv server, we just define the tools and their logic, then expose them using the `@mcp.tool` decorator. Here is what the use of this tool looks like:

![Streamlit parse](assets\streamlit_parse.png)

### Client Server

The client server, built using FastAPI, acts as the coordination layer. It connects to both MCP servers and integrates their functionalities using a LangChain ReAct agent. Here’s how it works:
- **MCP Client Setup:** A `MultiServerMCPClient` is created with endpoints for both the ArXiv and DocLing servers.
- **ReAct Agent:** The agent (created with `create_react_agent`) processes the research prompt by intelligently invoking the available tools.
- **FastAPI Endpoint:** The `/research` endpoint receives a user query, processes it via the agent, and returns the formatted response.

Below is an excerpt of the client server code:

```python
# client_server.py
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

class ResearchRequest(BaseModel):
    prompt: str

load_dotenv()
model = AzureChatOpenAI(azure_deployment=os.environ['AZURE_GPT_DEPLOYMENT'])
app = FastAPI(title="Research Assistant API")

async def process_prompt(prompt: str) -> Dict[str, Any]:
    mcp_client = MultiServerMCPClient({
        "arxiv": {
            "url": "http://arxiv-server:8000/sse",  # Docker service name
            "transport": "sse",
        },
        "docling": {
            "url": "http://docling-server:8001/sse",  # Docker service name
            "transport": "sse",
        }
    })
    async with mcp_client as client:
        agent = create_react_agent(model, client.get_tools())
        response = await agent.ainvoke({"messages": prompt}, debug=False)
        messages = [{i.type: i.content} for i in response['messages'] if i.content != '']
        return {"messages": messages}

@app.post("/research")
async def research(request: ResearchRequest):
    return await process_prompt(request.prompt)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

Here we wrap our client-server that uses the library [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) to transform the MCP tools into LangChain tools. We just inform the client how to connect to the servers and instantiate the rest as a normal Langchain agent.

### Streamlit UI

The Streamlit application provides a simple, user-friendly interface for interacting with our research assistant. Since its code involves standard web UI elements and interactions, you can find the full implementation in the repository. In essence, it simply sends research queries to the client-server and displays the results.

By modularizing the system with MCP servers and coordinating them through a FastAPI client using LangChain’s ReAct agent, we ensure that the research assistant remains flexible and scalable. This approach lets you easily integrate additional tools or data sources in the future.

Finally, we can wrap everything up using Docker Compose and have an interactive agent with a UI!

Feel free to explore the complete code in my [repo](https://github.com/raca159/mcp-demo) and experiment with the setup using Docker Compose as described in the project README. Happy coding!