import argparse
import logging

from expense_report import ExpenseReport


def parse_args():
    """Prases command line arguments.

    There are only two attributes for the returned parser.

    filenames:    ([str]) a list of filenames.
    directories: ([str]) a list of directories.
    """
    parser = argparse.ArgumentParser(
        description="""
        Creates an organized expense report with charts and graphs from a CSV
        file. The only columns required are 'date', expense' and 'price'.
        """
    )

    parser.add_argument(
        '--filename', '-f',
        nargs='+',
        default=list(),
        type=str,
        help='creates an expense report for the specified CSV files',
        dest='filenames'
    )

    parser.add_argument(
        '--directory', '-d',
        nargs='+',
        default=list(),
        type=str,
        help='creates expense reports for all CSV files in the specified directories',
        dest='directories'
    )

    parser.add_argument(
        '--debug',
        default='WARNING',
        type=str,
        help='sets the logging level, choosing from "CRITICAL", "ERROR", "WARNING", "INFO", or "DEBUG"',
        dest='debug'
    )

    return parser.parse_args()


def main():
    # Take command line input
    parser = parse_args()

    logging.basicConfig(level=parser.debug.upper())

    # TODO: Annual report
    # TODO: Compare with average monthly spending
    for filename in parser.filenames:
        expo = ExpenseReport(filename)
        expo.generate_report()

    #for directory in parse.directories:
        #for filename in os.listdir(directory):
            #if filename[-3:] != 'csv':
                #continue

            #expo = ExpenseReport(filename)
            #expo.generate_report()


if __name__ == '__main__':
    main()

