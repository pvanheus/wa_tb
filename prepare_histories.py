#!/usr/bin/env python3

import argparse
import sys

from bioblend import galaxy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare Galaxy histories for West Africa TB analysis."
    )
    parser.add_argument(
        "--galaxy-url",
        required=True,
        help="URL of the Galaxy instance.",
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="API key for the Galaxy instance.",
    )
    parser.add_argument(
        '--history-prefix',
        default='WA TB '
    )
    parser.add_argument(
        'min_number',
        default=1,
        type=int
    )
    parser.add_argument(
        'max_number',
        default=12,
        type=int
    )
    args = parser.parse_args()
    gi = galaxy.GalaxyInstance(url=args.galaxy_url, key=args.api_key)
    west_africa_tb_hist = [h for h in gi.histories.get_histories() if h["name"] == "West African TB"][0]
    datasets = gi.histories.show_history(west_africa_tb_hist["id"], contents=True)
    sample_datasets = {}
    reference_dataset = {}
    for dataset in datasets:
        name = dataset["name"]
        if name.startswith("sample_ids_"):
            sample_datasets[name] = dataset
        if name == "Mycobacterium_tuberculosis_ancestral_reference.gbk":
            reference_dataset = dataset

    for i in range(args.min_number, args.max_number + 1):
        sample_dataset = sample_datasets[f"sample_ids_{i-1:06d}.txt"]
        history_name = f"{args.history_prefix}{i}"
        histories = gi.histories.get_histories(name=history_name)
        if not histories:
            print('Creating history:', history_name)
            history = gi.histories.create_history(name=history_name)
            gi.histories.copy_dataset(history["id"], reference_dataset["id"])
            gi.histories.copy_dataset(history["id"], sample_dataset["id"])
            gi.tools.run_tool(
                history_id=history["id"],
                input_format="21.01",
                tool_id="fasterq_dump",
                tool_inputs={
                    "input": {
                        "input_select": "file_list",
                        "file_list": {"src": "hda", "id": sample_dataset["id"]}
                    }
                }
            )
        else:
            history = histories[0]
            print('History exists, skipping:', history["name"], file=sys.stderr)
