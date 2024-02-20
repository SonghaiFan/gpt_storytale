import json
import os
from typing import List, Dict


def parse_file_name(file_name: str) -> Dict:
    # Remove 'story_' from the start and split using underscores
    parts = file_name[len("story_") :].rsplit(".", 1)[0].split("_")

    return {
        "name": file_name,
        # the rest parts are the section
        "section": "_".join(parts[:-2]),
        "structure": parts[-2],
        "seed": int(parts[-1].replace("seed", "")),  # Extract seed number from "seedXX"
    }


def story_packer(directory: str) -> List[Dict]:
    stories = []

    # Iterate over all files in the directory
    for file_name in os.listdir(directory):
        # ignore folders and files not started with story
        if os.path.isdir(file_name) or not file_name.startswith("story_"):
            continue

        if file_name.startswith("story_"):  # Only process relevant files
            with open(os.path.join(directory, file_name), "r") as file:
                story_content = json.load(file)
                story_info = parse_file_name(file_name)

                # Combine story_info and story_content
                story = {**story_info, **story_content}
                stories.append(story)

    return stories


# Example
directory_path = "stories"
combined_stories = story_packer(directory_path)

# save to json
with open("stories/combined_stories.json", "w") as file:
    json.dump(combined_stories, file)

# move all the files in stories, log and alignment to arc folder within each of them
# Specify directories to be processed
directories = ["stories", "logs", "alignment"]

# Iterate over each directory
for directory in directories:
    # Make sure the target 'arc' directory exists
    os.makedirs(os.path.join(directory, "arc"), exist_ok=True)

    # Iterate over each file in the directory
    for file_name in os.listdir(directory):
        # Ensure you're working with files, not directories
        if os.path.isfile(os.path.join(directory, file_name)):
            # Rename (i.e., move) the file
            os.rename(
                os.path.join(directory, file_name),
                os.path.join(directory, "arc", file_name),
            )
