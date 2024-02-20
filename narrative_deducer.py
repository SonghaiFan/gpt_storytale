# Load environment variables from .env file
import warnings
import json
from typing import List
from meta.types import Chapter, Story
from langchain.output_parsers import PydanticOutputParser
from typing import Union, List
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


warnings.filterwarnings("ignore")


def make_chapter(
    id: str,
    theme: str,
    theme_context: str,
    entity: List[str],
    time_period: List[str],
    narrative_structure: str,
    prev_content: str,
    model_name: str = "gpt-4",
    temperature: int = 0,
) -> Chapter:
    """
    Function to generate a fictional news chapter continuing from a previous story.
    """
    # Parser for the model's output
    chapter_parser = PydanticOutputParser(pydantic_object=Chapter)

    time_period_str = f"{time_period[0]} to {time_period[1]}"

    prev_content_str = prev_content if prev_content else "None"

    # Create a prompt template
    prompt_template = f"""
    You are a senior reporter for The New York Times, your task is to write a fictional news report that continues from a previous one. 
    - Your writing style is concise and clear, without rhetorical techniques, in plain english. 
    - Avoid explicitly referencing the structure and themes; instead, integrate it subtly within the story.
    - The story should be written in a style suitable for CEFR Level A1 and each chapter approximately take 1 minutes to read (100 words).
    - The continuation chapter needs to be closely related to the previous one (intriguing and logically connected in narration),
    - The theme of the story must be strikingly prominent, you can not make up new themes except the only one given below.
    - All entities given below must be included in the story.
    
    Chapter ID: {id}
    Time Period: {time_period_str}
    Themes: {theme}
    Theme Context: {theme_context}
    Entity: {', '.join(entity)}

    Narrative Sturcture: {narrative_structure}

    Previous context: {prev_content_str}

    {chapter_parser.get_format_instructions()}
    """
    print("-" * 50)
    print(prompt_template)
    print("-" * 50)

    model = OpenAI(model_name=model_name, temperature=temperature)
    output = model(prompt_template)

    return chapter_parser.parse(output)


def create_story(alignment):
    story = Story(chapters=[])

    content_cache = {}

    print("Generating story...")

    print("Narrative structure:")

    for node, details in alignment.items():
        print("=" * 50)
        print(f"Generating chapter {node}...")
        print(f"This chapter based on previous chapter: {details['Prev']}")
        prev_content = "\n\n".join(
            [
                content_cache[prev_node]
                for prev_node in details["Prev"]
                if prev_node in content_cache
            ]
        )
        print(f"Previous content: {prev_content}")

        new_chapter = make_chapter(
            id=node,
            theme=details["Theme"],
            theme_context=details["ThemeDescription"],
            entity=details["Entity"],
            time_period=details["Time"],
            narrative_structure=details["StuctureInstruction"],
            prev_content=prev_content,
            temperature=0.5,
        )

        new_chapter_dict = new_chapter.dict()
        print("~" * 50)
        print(f"New chapter << {new_chapter_dict['title']} >> Finished!")
        print(new_chapter_dict["content"])
        print("~" * 50)
        story.chapters.append(new_chapter)
        content_cache[node] = new_chapter_dict["content"]

    return story


if __name__ == "__main__":
    # load alignment_results.json
    with open("alignment_results.json", "r") as file:
        alignment_results = json.load(file)
    story = create_story(alignment_results)
    with open("story.json", "w") as file:
        json.dump(story.dict(), file, indent=4)
