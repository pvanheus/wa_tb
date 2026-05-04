#!/usr/bin/env python3

import argparse
import re
import sys

from pprint import pprint
from typing import Any

from bioblend.galaxy import GalaxyInstance

# Create a Galaxy history that contains:
# 1. The FASTA format outgroup genome dataset. This typically is the "SRR10828835_L8.fasta" dataset from the "WA TB X working" histories, where X is a number. This dataset should be renamed to "West African TB" history.
# 2. A number of concatenated FASTA datasets from the "Concatenated consensus sequences" dataset of the "WA TB X working" histories, where X is a number. These datasets should be renamed to "WA TB X consensus sequences".
# 3. A list created from all the concatenated FASTA datasets.

def add_outputgroup_dataset(gi: GalaxyInstance, history_id: str, dataset_name:str = "SRR10828835_L8.fasta", source_history_name: str ="West African TB"):
    """Fetch the dataset with dataset_name from the history with source_history_name, and add it to the history with history_id."""
    source_history_candidates = gi.histories.get_histories(name=source_history_name)
    assert len(source_history_candidates) == 1, f"Expected exactly one history with name {source_history_name}, but found {len(source_history_candidates)}."
    source_history = source_history_candidates[0]
    source_datasets = gi.histories.show_history(source_history["id"], contents=True)
    source_dataset_candidates = [d for d in source_datasets if d["name"] == dataset_name]
    assert len(source_dataset_candidates) == 1, f"Expected exactly one dataset with name {dataset_name} in history {source_history_name}, but found {len(source_dataset_candidates)}."
    source_dataset = source_dataset_candidates[0]
    result = gi.histories.copy_dataset(history_id, source_dataset["id"])
    return result


def get_consensus_histories(gi: GalaxyInstance, history_name_pattern: str, start_num: int, end_num: int):
    """Fetch the histories with names matching history_name_pattern and numbers between start_num and end_num, and return a list of their "Concatenated consensus sequences" datasets."""
    pattern = re.compile(history_name_pattern)
    candidate_histories = [h for h in gi.histories.get_histories() if pattern.match(h["name"])]
    selected_histories = []
    for history in candidate_histories:
        match = pattern.match(history["name"])
        if match:
            num = int(match.group(1))
            if start_num <= num <= end_num:
                selected_histories.append(history)
    return selected_histories


def add_consensus_datasets(gi: GalaxyInstance, history_id: str, source_history_id: str):
    """Fetch the "Concatenated consensus sequences" dataset from the history with source_history_id, and add it to the history with history_id."""
    history_details = gi.histories.show_history(source_history_id)
    history_name = history_details["name"]
    source_datasets = gi.histories.show_history(source_history_id, contents=True)
    source_dataset_candidates = [d for d in source_datasets if d["name"] == "Concatenated consensus sequences"]
    assert len(source_dataset_candidates) == 1, f"Expected exactly one dataset with name 'Concatenated consensus sequences' in history {source_history_id}, but found {len(source_dataset_candidates)}."
    source_dataset = source_dataset_candidates[0]
    copy_result = gi.histories.copy_dataset(history_id, source_dataset["id"])
    result = gi.histories.update_dataset(history_id, copy_result["id"], name=f"{history_name} concatenated consensus sequences")
    return result

def create_consensus_sequence_list(gi: GalaxyInstance, history_id: str, consensus_datasets: list):
    """Create a list from the consensus_datasets in the history with history_id."""
    collection_description: dict[str, Any] = dict(
        collection_type="list",
        name="Consensus sequence datasets",
    )
    element_identifiers: list[dict[str, str]] = []
    for dataset in consensus_datasets:
        name = dataset["name"]
        id = dataset["id"]
        element_identifier = dict(
            name=name,
            src="hda",
            id=id
        )
        element_identifiers.append(element_identifier)
    collection_description["element_identifiers"] = element_identifiers

    list_result = gi.histories.create_dataset_collection(history_id, collection_description)                                                         
    return list_result


def sort_by_history_number(history: dict):
    pattern = re.compile(r'WA TB (\d+) working')
    match = pattern.match(history["name"])
    if match:
        return int(match.group(1))
    else:
        raise ValueError(f"History name {history['name']} does not match expected pattern.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Prepare a Galaxy history for phylogeny analysis by adding the outgroup dataset.")
    parser.add_argument('--galaxy-url', required=True, help='URL of the Galaxy instance.')
    parser.add_argument('--api-key', required=True, help='API key for the Galaxy instance.')
    parser.add_argument('--history-name', required=True, help='Name of the history to prepare.')
    parser.add_argument('--source-history-name', default='West African TB', help='Name of the history to copy the outgroup dataset from.')
    parser.add_argument('--outgroup-dataset-name', default='SRR10828835_L8.fasta', help='Name of the outgroup dataset to copy from the source history.')
    parser.add_argument('--result-history-pattern', default=r'WA TB (\d+) working', help='Regex pattern to match the names of the histories containing the results of genome assembly.')
    parser.add_argument('start_history_num', type=int, help='The number of the first history to copy the outgroup dataset from. For example, if the histories are named "WA TB 1 working", "WA TB 2 working", etc., and start_history_num is 1, then the outgroup dataset will be copied from "WA TB 1 working".')
    parser.add_argument('end_history_num', type=int, help='The number of the last history to copy the outgroup dataset from. For example, if the histories are named "WA TB 1 working", "WA TB 2 working", etc., and end_history_num is 3, then the outgroup dataset will be copied from "WA TB 1 working", "WA TB 2 working", and "WA TB 3 working".')
    args = parser.parse_args()

    gi = GalaxyInstance(url=args.galaxy_url, key=args.api_key)
    existing_histories = gi.histories.get_histories(name=args.history_name)
    if existing_histories:
        print(f"History with name {args.history_name} already exists. Cannot continue", file=sys.stderr)
        sys.exit(1)

    phylogeny_history = gi.histories.create_history(name=args.history_name)
    print(f"Created history with name {args.history_name} and id {phylogeny_history['id']}. Adding outgroup dataset...")
    outgroup_copy_result = add_outputgroup_dataset(gi, phylogeny_history["id"], dataset_name=args.outgroup_dataset_name, source_history_name=args.source_history_name)
    pprint(outgroup_copy_result)
    
    consensus_histories = get_consensus_histories(gi, args.result_history_pattern, args.start_history_num, args.end_history_num)
    consensus_histories.sort(key=sort_by_history_number)
    print(f"Found {len(consensus_histories)} histories matching pattern {args.result_history_pattern} and number range {args.start_history_num}-{args.end_history_num}.")

    consensus_datasets = []
    for history in consensus_histories:
        # the "id" of the returned result is the dataset id of the copied and renamed dataset in the target history
        copy_result = add_consensus_datasets(gi, phylogeny_history["id"], source_history_id=history["id"])
        print("Copied consensus dataset from history", history["name"], "with id", copy_result["id"])
        assert "id" in copy_result, f"Expected 'id' in copy result, but got {copy_result}."
        consensus_datasets.append(copy_result)

    list_result = create_consensus_sequence_list(gi, phylogeny_history["id"], consensus_datasets)
    print(f"Created list of consensus sequence datasets with id {list_result['id']} in history {phylogeny_history['id']}.")

    print("Done.")