#!/usr/bin/env python3

import pathlib
import collections
import shutil
import subprocess
import logging
import traceback


class ProtocolNotRunError(Exception):
    pass


class Protocol(object):
    def __init__(self, root):
        self._set_root_and_meta(root)
        self._parse_meta(self._meta_path)
        # Set empty values for private attributes
        self._exit_code = None

    def _set_root_and_meta(self, root):
        root = pathlib.Path(root)
        if not root.exists():
            raise FileNotFoundError('{} not found.'.format(str(root)))
        if root.is_dir():
            meta_path = root / pathlib.Path('meta.ini')
            if not meta_path.exists():
                raise FileNotFoundError('{} not found.'.format(str(meta_path)))
            self._meta_path = meta_path
            self._root = root
        else:
            self._meta_path = root
            self._root = root.parent

    def _parse_meta(self, meta_path):
        pass

    def run(self, force=False):
        if force or self.exit_code is None:
            self._exit_code = run_protocol(
                self.root,
                self.script,
                self.log_directory
            )

    @property
    def name(self):
        return str(self.root)

    @property
    def root(self):
        return self._root

    @property
    def script(self):
        return './test.sh'

    @property
    def log_directory(self):
        return self.root / pathlib.Path('LOGS')

    @property
    def exit_code_path(self):
        return self.log_directory / pathlib.Path('EXIT_CODE')

    @property
    def exit_code(self):
        # If exit code is known already, then just returns it.
        if self._exit_code is not None:
            return self._exit_code
        # If the protocol got run before, then read the logged exit code.
        # If not, then the protocol did not ran yet, and we return None.
        try:
            with open(str(self.exit_code_path)) as infile:
                self._exit_code = int(infile.read())
            return self._exit_code
        except FileNotFoundError:
            return None


def should_ignore(path, ignore):
    """
    Return True is the path contains one of the motifs to ignore.

    The motifs in *ignore* are matched exactly as strings.

    Parameters
    ----------
    path: str or pathlib.Path
        Path to test againgst the motifs.
    ignore: list of strings
        List of motifs to test.

    Returns
    -------
    bool
        True is the path contains at least one of the motifs
        and should be ignored.
    """
    for token in ignore:
        if token in str(path):
            return True
    return False


def overlay_directories(sources, destination, ignore=[]):
    """
    Copy an overlayed version of a collection of directories

    Inputs
    ------

    sources: list of pathes
        A list of the source directories to copy. The directories are copied
        in order so the version in the latest path is kept.
    destination: path
        The path where to place the copy. If the directory already exists,
        the sources are copied in the destination. If the directory does not
        exist, it is created and the sources are copied as the destination.
    """
    # Convert arguments to pathlib.Path object for easier manipulation.
    sources = [pathlib.Path(path) for path in sources]
    destination = pathlib.Path(destination)

    # Test the sources. Are all the path directories? Do they all exist?
    non_dir = [str(path) for path in sources if not path.is_dir()]
    if non_dir:
        if len(non_dir) == 1:
            message = ("One source path is not a directory: {}"
                       .format(non_dir[0]))
        else:
            message = ("Some source pathes are not directories: {}"
                       .format(','.join(non_dir)))

        raise NotADirectoryError(message)

    # Test the destination. Does it exist? Is it a directory?
    if destination.exists() and not destination.is_dir():
        raise NotADirectoryError("Destination must be a directory.")

    # List the files. For each file, what is its source,
    # and what is its destination? This avoids to copy several versions of
    # the same files.
    files = collections.OrderedDict()
    for path in sources:
        files.update(
            collections.OrderedDict(
                [(p.relative_to(path), p)
                 for p in path.glob('**/*')
                 if not should_ignore(p, ignore)]
            )
        )

    # Create the destination if needed.
    if not destination.exists():
        destination.mkdir(parents=True)#, exist_ok=True)

    # Copy the files.
    for dest, origin in files.items():
        full_dest = destination / dest
        if origin.is_dir():
            if not full_dest.exists():
                full_dest.mkdir()
        else:
            if not full_dest.parent.exists():
                full_dest.parent.mkdir()
            shutil.copy(str(origin), str(full_dest))


def get_tests(root):
    """
    Generate a list of directories containing test protocols
    """
    #return (path.parent for path in pathlib.Path(root).glob('**/meta.ini'))
    return (Protocol(path) for path in pathlib.Path(root).glob('**/meta.ini'))


def run_protocol(root, script, log_directory=None):
    # Decide where to log data 
    root = pathlib.Path(root)
    if log_directory is None:
        log_directory = root / pathlib.Path('LOGS')
    else:
        log_directory = pathlib.Path(log_directory)
    if not log_directory.exists():
        log_directory.mkdir(parents=True)
    elif not log_directory.is_dir():
        raise NotADirectoryError('Logging directory ({}) is not a directory.'
                                 .format(log_directory))
    # Actually run the protocol
    process = subprocess.Popen(
        script,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(root.absolute()))
    with process:
        # This aims at logging stdout and stderr.
        # Ideally, each line is logged separatelly with a record of the
        # time and the source (out or err). This allows neat outputs latter on.
        # The current code does not work as intended, but is left to be
        # fixed latter. Yes, that is awesome programming practice.
        # TODO: Fix logging of subprocesses.
        logging.info(process.stdout.read())
        logging.error(process.stderr.read())
    exit_code = process.wait()
    # Log the exit code
    exit_code_file = log_directory / pathlib.Path('EXIT_CODE')
    with open(str(exit_code_file), 'w') as outfile:
        print(exit_code, file=outfile)
    
    return exit_code


def main():
    original_input = './'
    user_input = '../test_aa/overlay2/'
    destination = '../test_aa/dest/'
    overlay_directories(
        [original_input, user_input], destination, ignore=['.git', ]
    )

    for test in get_tests(destination / pathlib.Path('protocols')):
        print(test.name, end=' ')
        try:
            test.run()
        except Exception as e:
            print('[EXCEPTION]')
            traceback.print_tb(e)
        else:
            if test.exit_code != 0:
                print('[ERROR]')
            else:
                print('[FINISH]')  # Finished, but how is the result?


if __name__ == '__main__':
    main()
