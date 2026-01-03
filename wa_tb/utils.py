import argparse

def make_parser(description: str = "") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description
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
    return parser
