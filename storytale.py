import os
import sys
import json
import random
from typing import Optional

from narrative_alignmenter import align_theme_entity

from narrative_deducer import create_story


def get_alignment(topic: str, structure: str, seed: Optional[int] = None):
    print("=" * 50)
    print("Selected narrative structure:", structure)

    narrative_obj = next(
        (s for s in narrative_context if s["name"] == structure),
        None,
    )

    if not narrative_obj:
        print(
            f"No structure found with the name: {structure}. Using the first structure in the list.")
        narrative_obj = narrative_context[0]

    alignment_results = align_theme_entity(
        narrative_obj=narrative_obj, seed=seed)
    return alignment_results


def generate_story_files(topic: str, structure: str, seed: Optional[int] = None):
    if seed is None:
        seed = random.randint(0, 1000)

    # Define folders
    alignment_folder = "alignment"
    stories_folder = "stories"
    log_folder = "logs"

    # Generate filenames
    filename_suffix = f"{topic}_{structure}_seed{seed}.json"
    alignment_filename = f"alignment_{filename_suffix}"
    story_filename = f"story_{filename_suffix}"
    log_filename = f"log_{filename_suffix}"

    # Check/Create folders
    for folder in [alignment_folder, stories_folder, log_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # File paths
    alignment_path = os.path.join(alignment_folder, alignment_filename)
    story_path = os.path.join(stories_folder, story_filename)
    log_path = os.path.join(log_folder, log_filename)

    # Redirect stdout to log file
    sys.stdout = open(log_path, "w")

    # Get alignment and save
    alignment_results = get_alignment(topic, structure, seed)
    with open(alignment_path, "w") as file:
        json.dump(alignment_results, file)

    # Load alignment and generate story
    with open(alignment_path, "r") as file:
        loaded_alignment_results = json.load(file)

    story = create_story(loaded_alignment_results)

    # Save story
    with open(story_path, "w") as file:
        json.dump(story.dict(), file, indent=4)

    sys.stdout.close()


if __name__ == "__main__":
    with open("meta/narrative_context_a.json", "r") as file:
        narrative_context = json.load(file)

    narrative_structures = [item["name"] for item in narrative_context]
    print("narrative_structures", narrative_structures)

    topic = "Set_A2"
    for structure in narrative_structures:
        generate_story_files(topic, structure)
