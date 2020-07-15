"""Homework, CLI arguments and logging."""

import argparse
import os
import os.path
import shutil
import time
from typing import List, Callable, Generator


class ActionPlanner:
    """Stores functions that have been decorated. Calls them if they were mentioned in CLI."""

    def __init__(self):
        self.actions = {}

    def action_decorator(self, cli_flag: str) -> Callable:
        """Use with care!
        All actions will be performed to data in the order they were added to argparser."""

        actions = self.actions

        def outer(func: Callable):
            actions.update({cli_flag: func})

        return outer

    def perfrom_actions(self, cli_args: argparse.Namespace, data: List[str]) -> List:
        actions = [self.actions.get(k) for k, v in vars(cli_args).items() if v and self.actions.get(k)]

        new_data = data.copy()
        for action in actions:
            new_data = action(new_data)

        return new_data


def handle_args() -> argparse.Namespace:
    """Returns CLI arguments namespace.
    Arguments are put in safe order."""

    parser = argparse.ArgumentParser(description='Lists files in specified directory.')
    parser.add_argument('files_or_dirs', metavar='File(s) or/and Directory(s)', nargs='*', default=[os.getcwd(), ],
                        help='files/directories located in specified files/directories will be listed '
                             '(default: current working directory)')

    parser.add_argument('-a', action='store_false', help='include entries starting with "."')
    sorting_group = parser.add_mutually_exclusive_group()
    sorting_group.add_argument('-f', action='store_false', help='do not sort')
    sorting_group.add_argument('-t', action='store_true', help='sort by modification time')
    sorting_group.add_argument('-r', action='store_true', help='reverse sort')
    f_group = parser.add_mutually_exclusive_group()
    f_group.add_argument('-1', action='store_true', help='output one entry per line')
    f_group.add_argument('-F', action='store_true', help='appends a character revealing the nature of an entry')
    f_group.add_argument('-l', action='store_true', help='long format')
    f_group.add_argument('-m', action='store_true', help='format wih commas')

    return parser.parse_args()


def prepare_entries_to_display(cli_args: argparse.Namespace) -> Generator:
    """First, yields all additional files mentioned in CLI.
    Then scans each dir mentioned in CLI and yields files from it.

    But, it yields the whole list of stuff at once. I have no idea why. Chain does the same thing."""

    yield from filter(os.path.isfile, cli_args.files_or_dirs)

    paths_to_scan = filter(os.path.isdir, cli_args.files_or_dirs)
    yield from ((os.listdir(path)) for path in paths_to_scan)


if __name__ == '__main__':
    ap = ActionPlanner()

    @ap.action_decorator('f')
    def do_sort(to_display: List[str]) -> List:
        return sorted(to_display)

    @ap.action_decorator('r')
    def do_sort(to_display: List[str]) -> List:
        return sorted(to_display, reverse=True)

    @ap.action_decorator('F')
    def nature_of_file(to_display: List[str]) -> List:
        result = []
        for path in to_display:
            if os.path.isdir(path):
                result.append(path + '/')
            elif os.access(path, os.X_OK):
                result.append(path + '*')
            else:
                result.append(path)

        return result

    @ap.action_decorator('l')
    def long_format(to_display: List[str]) -> List:
        rows = ['']
        for path in to_display:
            mtime = time.strftime('%d_%b_%Y_%H:%M:%S', time.localtime(os.path.getmtime(path)))
            size = os.path.getsize(path)

            if os.path.isdir(path):
                file_or_dir = 'd'
            else:
                file_or_dir = ''

            rows.append(f'{file_or_dir}\t{mtime}\t{size:9_}\t{path}\n')
        return rows

    @ap.action_decorator('t')
    def sort_by_mtime(to_display: List[str]) -> List:
        return sorted(to_display, key=lambda p: os.path.getmtime(p))

    @ap.action_decorator('a')
    def include_dots(to_display: List[str]) -> List:
        return list(filter(lambda p: p[0] != '.', to_display))

    @ap.action_decorator('1')
    def one_column(to_display: List[str]) -> List:
        return list(map(lambda p: p + '\n', to_display))

    @ap.action_decorator('m')
    def one_column(to_display: List[str]) -> List:
        columns = shutil.get_terminal_size().columns

        rows = ['']
        row = ''
        len_to_display = len(to_display)
        for i, path in enumerate(to_display):
            if len(row) + len(path) >= columns:
                row += '\n'
                rows.append(row)
                row = ''

            if i < len_to_display - 1:
                row += f'{path}, '
            else:
                row += f'{path}'
                rows.append(row)

        return rows


    args = handle_args()

    entries_to_display = next(prepare_entries_to_display(args))
    print(*ap.perfrom_actions(args, entries_to_display))
