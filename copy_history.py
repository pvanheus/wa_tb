#!/usr/bin/env python3

import argparse

from bioblend import galaxy

from wa_tb.utils import make_parser


if __name__ == "__main__":
    parser = make_parser("Make a copy of a Galaxy history.")
    parser.add_argument(
        'old_history_name'
    )
    parser.add_argument(
        'new_history_name',

    )
    args = parser.parse_args()
    gi = galaxy.GalaxyInstance(url=args.galaxy_url, key=args.api_key)
    old_history = None
    histories = gi.histories.get_histories(name=args.old_history_name)
    assert len(histories) == 1, "Could not find unique history: {len(histories)} found"
    old_history = histories[0]
    # This uses a copy_history function that was added in bioblend PR #528 and is
    # not yet part of a released version of bioblend (as of January 2026).
    new_history = gi.histories.copy_history(old_history['id'], name=args.new_history_name)
    print(f"Created new history: {new_history['name']} (id: {new_history['id']})")