import arxiv
from mcp.server.fastmcp import FastMCP
from typing import Optional
from pydantic import BaseModel
import asyncio

# Use environment variable for port if available
mcp = FastMCP(
    "Research Article Provider", port=8000
)

class Article(BaseModel):
    title: str
    summary: str
    published_date: str
    pdf_link: Optional[str]

    @classmethod
    def from_arxiv_result(cls, result: arxiv.Result) -> 'Article':
        pdf_links = [str(i) for i in result.links if '/pdf/' in str(i)]
        if len(pdf_links):
            pdf_link = pdf_links[0]
        else:
            pdf_link = None
        return cls(
            title=result.title,
            summary=result.summary,
            published_date=result.published.strftime('%Y-%m-%d'),
            pdf_link=pdf_link
        )
    
    def __str__(self):
        return f'Title: {self.title}\nDate: {self.published_date}\nPDF Url: {self.pdf_link}\n\n'+'\n'.join(self.summary.splitlines()[:3])+'\n[...]'

def get_articles_content(query: str, max_results: int) -> list[Article]:
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by = arxiv.SortCriterion.Relevance)
    articles = map(lambda x: Article.from_arxiv_result(x), client.results(search))
    articles_with_link = filter(lambda x: x.pdf_link is not None, articles)
    return list(articles_with_link)

@mcp.tool(
    name="search_arxiv",
    description="Get `max_results` articles for a given search query on Arxiv."
)
async def get_articles(query: str, max_results: int) -> str:
    """Get `max_results` articles for a given search query on Arxiv."""
    print(f"Searching for '{query}'...")
    articles = get_articles_content(query, max_results)
    print(f"Found {len(articles)} articles.")
    return '\n\n-------\n\n'.join(map(str, articles)).strip()

if __name__ == "__main__":
    asyncio.run(mcp.run_sse_async())