from mcp.server.fastmcp import FastMCP
from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken
import asyncio
# Use environment variable for port if available
mcp = FastMCP(
    "Research Article Extraction Provider", port=8001
)

def get_article_content_str(article_url: str):
    converter = DocumentConverter()
    result = converter.convert(article_url)
    research = result.document.export_to_markdown()
    return research

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
    description="Extracts the full text content from a research article PDF using OCR technology based on its pdf link `article_url`"
)
async def get_article_content(article_url: str) -> str:
    """Get article content extracted from OCR given its pdf url link `article_url`."""
    articlecontent = get_article_content_str(article_url)

    return articlecontent.strip()

@mcp.tool(
    name="get_article_preview",
    description="Retrieves the first portion of a research article based on its pdf link `article_url` with a specified token limit (`chunk_size`), useful for quick previews"
)
async def get_article_first_lines(article_url: str, chunk_size: int = 1536) -> str:
    """Get `chunk_size` tokens for an article based on its pdf url link `article_url`."""
    articlecontent = get_article_content_str(article_url)
    first_lines_content = first_lines(articlecontent.strip(), chunk_size)

    return first_lines_content.strip()

if __name__ == "__main__":
    asyncio.run(mcp.run_sse_async())
