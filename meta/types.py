from typing import *
from pydantic import BaseModel, Field
from datetime import date

# my_cartographer


class Node(BaseModel):
    index: str = Field(
        description="Index of the node.Consists of a capital letter representing the theme and a number representing the chronological order (e.g. A1,B2)"
    )
    label: str = Field(labels="Title of chapter.")
    time_period: List[str] = Field(
        description="Time period of the chapter (start date, end date), in format YYYY-MM-DD."
    )
    themes: List[str] = Field(description="Themes related within chapter.")
    entity: List[str] = Field(description="Entity mentioned within chapter.")
    context: str = Field(
        description="Context of chapter. Simple summary of the context of chapter."
    )


class Edge(BaseModel):
    start_node: str = Field(description="Index of start node.")
    end_node: str = Field(description="Index of end node.")
    labels: str = Field(
        labels="Keyword Explain the connections (edges) between nodes.")


class Graph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


# my_writer


class Chapter(BaseModel):
    id: str = Field(description="ID of the chapter .")
    title: str = Field(description="Headlines for news story chapters")
    time_period: List[str] = Field(
        description="Time period of the chapter (start date, end date), in format YYYY-MM-DD."
    )
    themes: List[str] = Field(description="Themes related within chapter.")
    entity: List[str] = Field(description="Entity mentioned within chapter.")
    content: str = Field(
        description="Content of the chapter(In format as news article lead paragraph)."
    )


class Story(BaseModel):
    chapters: List[Chapter] = Field(description="List of chapters.")


# my_journalist


class Article(BaseModel):
    pub_date: date = Field(
        description="Published date of the news article in date format."
    )
    headline: str = Field(description="Headline of the news article.")
    themes: List[str] = Field(description="Themes of the news article.")
    entity: List[str] = Field(description="Entity of the news article.")
    keywords: List[str] = Field(
        description="Key words of the news article, avoiding repetition with themes and entities."
    )
    lead_paragraph: str = Field(
        description="Lead paragraph of the news article, approximately 100 words in length."
    )


class ArticleCorpus(BaseModel):
    articles: List[Article] = Field(description="A list of news articles.")
