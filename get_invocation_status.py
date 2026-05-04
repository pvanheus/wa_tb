#!/usr/bin/env python3

from bioblend import galaxy

from wa_tb.utils import make_parser

if __name__ == '__main__':
    parser = make_parser("Check the status of workflow invocations on Galaxy histories.")
    parser.add_argument(
        '--history-prefix',
        default='WA TB'
    )
    args = parser.parse_args()
    gi = galaxy.GalaxyInstance(url=args.galaxy_url, key=args.api_key)
    workflows = gi.workflows.get_workflows()
    latest_workflow_id_to_name = {}
    for workflow in workflows:
        latest_workflow_id_to_name[workflow['latest_workflow_id']] = workflow['name']

    working_histories = [
        h for h in gi.histories.get_histories() if h["name"].startswith(args.history_prefix) and "working" in h["name"]
    ]
    for history in working_histories:
        datasets = gi.histories.show_history(history["id"], contents=True)
        has_completed = False
        has_run = False
        is_ready = False
        invocation_status = "not_started"
        workflow_name = "N/A"
        for dataset in datasets:
            dataset_name = dataset["name"]
            if dataset_name == "fasterq-dump log" and dataset["state"] == "ok":
                is_ready = True
            if dataset_name.startswith("SNP distance matrix on") and dataset["state"] == "ok":
                has_completed = True
            # if dataset_name.startswith("seqret on") and dataset["state"] == "ok":
            #     has_run = True
        invocations = gi.invocations.get_invocations(history_id=history["id"])
        assert len(invocations) <= 1, f"More than one invocation found for history {history["name"]}."
        workflow_invocation = invocations[0] if invocations else None
        if workflow_invocation:
            invocation_status = workflow_invocation["state"]
            invocation_summary = gi.invocations.get_invocation_summary(workflow_invocation["id"])
            completed_jobs = invocation_summary["states"].get("ok", 0)
            workflow_id = workflow_invocation['workflow_id'] 
            workflow_name = latest_workflow_id_to_name.get(workflow_id, workflow_id)
        print(history["name"], history["id"], is_ready, has_run, has_completed,
              invocation_status, completed_jobs, workflow_name, sep="\t")
