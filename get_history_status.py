#!/usr/bin/env python3

import argparse
import re

from bioblend import galaxy


def history_name_sort_key(history: dict) -> int:
    """Extract sorting key."""
    history_num_match = re.search(r"(\d+)$", history["name"])
    assert history_num_match is not None, "History names must end with a number"
    history_num = int(history_num_match.group(1))
    return history_num


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare Galaxy histories by removing datasets and renaming them."
    )
    parser.add_argument(
        "--galaxy-url",
        default="https://usegalaxy.eu",
        help="URL of the Galaxy instance.",
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="API key for the Galaxy instance.",
    )
    parser.add_argument("--history-prefix", default="WA TB ")
    history_name_re = re.compile(
        r"^" + re.escape(parser.parse_args().history_prefix) + r"(\d+)$"
    )
    args = parser.parse_args()
    gi = galaxy.GalaxyInstance(url=args.galaxy_url, key=args.api_key)
    working_histories = [
        h for h in gi.histories.get_histories() if re.match(history_name_re, h["name"])
    ]
    working_histories.sort(key=history_name_sort_key)
    for history in working_histories:
        datasets = gi.histories.show_history(history["id"], contents=True)
        state = "unknown"
        download_present = False
        for dataset in datasets:
            if dataset["name"] == "fasterq-dump log":
                download_present = True
                state = dataset["state"]
            elif dataset["name"].startswith("SNP distance matrix on") and dataset["state"] == "ok":
                state = "completed"
        print(history["name"], history["id"], download_present, state, sep="\t")
