#!/usr/bin/env python3

import pathlib
import collections
import shutil
import subprocess
import logging


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
    return (path.parent for path in pathlib.Path(root).glob('**/meta.ini'))


def run_protocol(root, script, log_directory=None):
    # Decide where to log data 
    root = pathlib.Path(root)
    if log_directory is None:
        log_directory = root / pathlib.Path(log_directory)
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
        print(test, end=' ')
        script =  './test.sh'
        try:
            status = run_protocol(test, script)
        except Exception as e:
            print('[EXCEPTION]')
            print(e)
        else:
            if status != 0:
                print('[ERROR]')
            else:
                print('[FINISH]')  # Finished, but how is the result?


if __name__ == '__main__':
    main()
