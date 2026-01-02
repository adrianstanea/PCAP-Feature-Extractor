from .output_writer import OutputWriter
from .csv_writer import CSVWriter


def output_writer_factory(output_mode, output) -> OutputWriter:
    match output_mode:
        case "csv":
            return CSVWriter(output)
        case _:
            raise RuntimeError("no valid output_mode provided")
