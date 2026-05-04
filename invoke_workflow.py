#!/usr/bin/env python3

import argparse

from bioblend import galaxy

from wa_tb.utils import make_parser

if __name__ == "__main__":
    parser = make_parser("Invoke workflow on a Galaxy history.")
    parser.add_argument(
        "--workflow-name",
        default="TB Variant Analysis v1.6.0"
    )
    parser.add_argument("history_name",
                        help="Name of the history to run the workflow on.")
    args = parser.parse_args()
    gi = galaxy.GalaxyInstance(url=args.galaxy_url, key=args.api_key)
    histories = gi.histories.get_histories(name=args.history_name)
    assert len(histories) == 1, f"Expected exactly one history with name {args.history_name}, but found {len(histories)}."
    history = histories[0]
    datasets = gi.histories.show_history(history["id"], contents=True)
    has_completed = False
    has_run = False
    is_ready = False
    input_reads = {}
    input_reference = {}
    for dataset in datasets:
        dataset_name = dataset["name"]
        if dataset_name == 'Pair-end data (fasterq-dump)':
            input_reads = dataset
        elif dataset_name == "Mycobacterium_tuberculosis_ancestral_reference.gbk":
            input_reference = dataset
        if dataset_name == "fasterq-dump log" and dataset["state"] == "ok":
            is_ready = True
        if dataset_name.startswith("SNP distance matrix on") and dataset["state"] == "ok":
            has_completed = True
        if dataset_name.startswith("seqret on") and dataset["state"] == "ok":
            has_run = True

    if is_ready and (input_reads == {} or input_reference == {}):
        raise ValueError("Could not find required input datasets in history.")
    # TODO: use get_workflow_inputs to get the UUIDs of the inputs instead of names.
    print("History:", history["name"], "Ready:", is_ready, "Has run:", has_run, "Has completed:", has_completed)
    if is_ready and not has_run:
        workflow = gi.workflows.get_workflows(name=args.workflow_name)[0]
        gi.workflows.invoke_workflow(
            workflow_id=workflow["id"],
            history_id=history["id"],
            inputs_by="name",
            inputs = {
                "Reads": {"id": input_reads["id"], "src": "hdca"},
                "Reference Genome": {"id": input_reference["id"], "src": "hda"},
            },
        )
        print("Workflow started for history:", history["name"])