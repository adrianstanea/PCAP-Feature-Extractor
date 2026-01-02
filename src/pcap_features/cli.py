import argparse
import os


def get_args() -> None:
    parser = argparse.ArgumentParser()

    input_mmode = parser.add_mutually_exclusive_group(required=True)
    input_mmode.add_argument(
        "-f",
        "--file",
        action="store",
        dest="input_file",
        help="capture offline data from INPUT_FILE",
    )

    output_mode = parser.add_mutually_exclusive_group(required=True)
    output_mode.add_argument(
        "-c",
        "--csv",
        action="store_const",
        const="csv",
        dest="output_mode",
        help="output flows as csv",
    )

    parser.add_argument(
        "output",
        help="output file name (in CSV mode)",
    )

    parser.add_argument(
        "--fields",
        action="store",
        dest="fields",
        help="comma separated fields to include in output (default: all)",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="more verbose")

    args = parser.parse_args()
    validate_args(args, parser)
    process_args(args)

    return args


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    pass


def process_args(args: argparse.Namespace) -> None:
    if args.output_mode == "csv":
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
