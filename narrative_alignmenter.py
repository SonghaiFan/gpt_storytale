import json
import datetime
import random


# with open("meta/narrative_context.json", "r") as file:
#     narrative_context = json.load(file)

# narrative_structure = [item["name"] for item in narrative_context]
# print("narrative_structure", narrative_structure)


def generate_time_periods(start_date, end_date, num_periods):
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days
    average_duration = total_days // num_periods
    periods = []

    for i in range(num_periods):
        period_start = start + datetime.timedelta(days=i * average_duration)
        period_end = period_start + datetime.timedelta(days=average_duration)

        # Ensure the last period does not exceed the end date
        if period_end > end or i == num_periods - 1:
            period_end = end

        periods.append([str(period_start.date()), str(period_end.date())])

    return periods


def process_nodes_in_order(narrative_obj):
    """Process nodes ensuring parent nodes are always processed before their child nodes."""
    nodes_to_process = narrative_obj["nodes"].copy()
    processed_nodes = []
    parent_mapping = {}

    # Build a dictionary to map each node to its parents
    for edge in narrative_obj["edges"]:
        if edge["to"] not in parent_mapping:
            parent_mapping[edge["to"]] = []
        parent_mapping[edge["to"]].append(edge["from"])

    while nodes_to_process:
        for node in nodes_to_process[:]:
            # If the node has no parents or all its parents are already processed, process this node
            if node not in parent_mapping or all(
                parent in processed_nodes for parent in parent_mapping[node]
            ):
                processed_nodes.append(node)
                nodes_to_process.remove(node)

    return processed_nodes


def align_theme_entity(narrative_obj, seed=None):
    """Align themes and entities with a narrative structure."""
    if seed:
        random.seed(seed)

    # Build a dictionary to map each node to its parents
    parent_mapping = {}
    for edge in narrative_obj["edges"]:
        if edge["to"] not in parent_mapping:
            parent_mapping[edge["to"]] = []
        parent_mapping[edge["to"]].append(edge["from"])

    # Pre-calculate the time periods for all symbols and chapters
    max_chapter_number = max([int(node[-1])
                             for node in narrative_obj["nodes"]])
    time_periods = {}

    for symbol in set(node[0] for node in narrative_obj["nodes"]):
        node_context = next(
            ctx for ctx in narrative_obj["context"] if ctx["symbol"] == symbol)
        periods = generate_time_periods(
            node_context["time"][0], node_context["time"][1], max_chapter_number)
        for i in range(max_chapter_number):
            time_periods[symbol + str(i + 1)] = periods[i]

    # Assign themes, entities, and time periods based on the node's symbol
    alignment = {}
    ordered_nodes = process_nodes_in_order(narrative_obj)

    for node in ordered_nodes:
        # Fetch the context corresponding to the symbol of the node
        node_context = next(
            ctx for ctx in narrative_obj["context"] if ctx["symbol"] == node[0])

        # Randomly sample entities
        entities_for_node = [ent["name"] for ent in random.sample(
            node_context["entities"], min(len(node_context["entities"]), 4))]

        # Ensure there's at least one shared entity with parent nodes, if they exist
        if node in parent_mapping:
            shared_entities = [
                ent for parent_node in parent_mapping[node] for ent in alignment[parent_node]["Entity"]
            ]
            entities_for_node.append(random.choice(shared_entities))

        alignment[node] = {
            "Theme": node_context["theme"],
            "ThemeDescription": node_context["description"],
            "Entity": list(set(entities_for_node)),
            # Use the pre-calculated time period for the node
            "Time": time_periods[node],
            "Prev": parent_mapping.get(node, []),
            "StuctureInstruction": f"The narrative structure is {narrative_obj['name']}, where {narrative_obj['description']} (eg. {narrative_obj['structure']}). The current chapter node is {node}, which is the {node[-1]}th chapter node in the narrative structure."
        }

    return alignment


if __name__ == "__main__":
    NARRATIVE_STRUCTURE = "Arch"

    print("=" * 50)
    print("Selected narrative structure:", NARRATIVE_STRUCTURE)

    # Get the alignment results
    narrative_obj = next(
        (s for s in narrative_context if s["name"]
         == NARRATIVE_STRUCTURE),
        None,
    )

    if not narrative_obj:
        print(
            f"No structure found with the name: {NARRATIVE_STRUCTURE}. Using the first structure in the list.")
        narrative_obj = narrative_context[0]

    alignment_results = align_theme_entity(
        narrative_obj=narrative_obj, seed=42)
    print("Generated alignment_results:", alignment_results)

    # Save the alignment results
    with open("alignment_results.json", "w") as file:
        json.dump(alignment_results, file)
