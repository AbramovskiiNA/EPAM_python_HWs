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

    def perfrom_actions(self, cli_args: argparse.Namespace, data: List) -> List:
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
    Then scans each dir mentioned in CLI and yields files from it."""

    yield from filter(os.path.isfile, cli_args.files_or_dirs)

    paths_to_scan = filter(os.path.isdir, cli_args.files_or_dirs)
    for path in paths_to_scan:
        for entry in os.scandir(path):
            yield entry.path


if __name__ == '__main__':
    ap = ActionPlanner()

    @ap.action_decorator('f')
    def do_sort(abs_paths: List[str]) -> List[str]:
        return sorted(abs_paths, key=lambda p: os.path.basename(p))

    @ap.action_decorator('r')
    def rev_sort(abs_paths: List[str]) -> List[str]:
        return sorted(abs_paths, key=lambda p: os.path.basename(p), reverse=True)

    @ap.action_decorator('F')
    def nature_of_file(abs_paths: List[str]) -> List[str]:
        result = []
        for path in abs_paths:
            name = os.path.basename(path)
            if os.path.isdir(path):
                result.append(name + '/')
            elif os.access(path, os.X_OK):
                result.append(name + '*')
            else:
                result.append(name)

        return result

    @ap.action_decorator('l')
    def long_format(abs_paths: List[str]) -> List[str]:
        rows = ['']
        for path in abs_paths:
            mtime = time.strftime('%d_%b_%Y_%H:%M:%S', time.localtime(os.path.getmtime(path)))
            size = os.path.getsize(path)

            if os.path.isdir(path):
                file_or_dir = 'd'
            else:
                file_or_dir = ''

            rows.append(f'{file_or_dir}\t{mtime}\t{size:12_}\t{os.path.basename(path)}\n')
        return rows

    @ap.action_decorator('t')
    def sort_by_mtime(abs_paths: List[str]) -> List[str]:
        return sorted(abs_paths, key=lambda p: os.path.getmtime(p))

    @ap.action_decorator('a')
    def include_dots(abs_paths: List[str]) -> List[str]:
        return list(filter(lambda p: os.path.basename(p)[0] != '.', abs_paths))

    @ap.action_decorator('1')
    def one_column(abs_paths: List[str]) -> List[str]:
        return list(map(lambda p: os.path.basename(p) + '\n', abs_paths))

    @ap.action_decorator('m')
    def one_column(abs_paths: List[str]) -> List[str]:
        columns = shutil.get_terminal_size().columns

        rows = ['']
        row = ''
        len_to_display = len(abs_paths)
        for i, path in enumerate(map(os.path.basename, abs_paths)):
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

    entries_to_display = list(prepare_entries_to_display(args))
    result_to_display = list(ap.perfrom_actions(args, entries_to_display))
    print(*map(os.path.basename, result_to_display))
