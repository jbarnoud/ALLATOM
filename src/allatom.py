#!/usr/bin/env python3

import pathlib
import collections
import shutil
import subprocess
import traceback
import configparser
import io


# The directory of this program source code
SRC_DIR = pathlib.Path(__file__).parent.absolute()


class ProtocolNotRunError(Exception):
    pass


class Protocol(object):
    def __init__(self, root):
        self._set_root_and_meta(root)
        self._parse_meta(self._meta_path)
        # Set empty values for private attributes
        self._exit_code = None

    def _set_root_and_meta(self, root):
        """
        Figure out what the root directory and the metadata file are.

        A Prococol instance can be created from the path of a metadata file
        or from the path of a directory containing a metadata file. In the
        former case, the root directory is considered to be the parent
        directory of the metadata file. In the latter case, the provided
        directory is considered the root directory, and the metadata file is
        searched in the directory.

        The method set `self._root` and `self._meta_path` regardless of their
        previous values if any.

        Parameters
        ----------
        root: path (str or pathlib.Path)
            Path to the root directory or the metadata file.

        Raises
        ------
        FileNotFoundError
            The provided path does not exist, or no metadata file could be
            found.
        """
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
        """
        Read the metadata file

        Parameters
        ----------
        meta_path: path (str or pathlib.Path)
            Path to the metadata file.
        """
        default_path = SRC_DIR / pathlib.Path('meta_default.ini')
        self._meta = configparser.ConfigParser()
        self._meta.read(str(default_path))
        self._meta.read(str(meta_path))

    def run(self, force=False):
        """
        Execute the protocol script

        The protocol script is executed only if it did not run already, i.e. if
        the exit code is not already available. The execution can be force by
        setting the *force* argument to `True`.

        The exit code is recorded in the EXIT_CODE file.

        Parameters
        ----------
        force: bool
            If `True`, the protocol is executed even if it got executed
            previously already.
        """
        if force or self.exit_code is None:
            self._exit_code = run_protocol(
                self.root,
                self.script,
                self.log_directory
            )

    @property
    def name(self):
        """
        Name of the protocol

        The name is read in the metadata file if possible. If not, then
        the path to the root directory is returned instead.
        """
        return self._meta['Protocol'].get('name', str(self.root))

    @property
    def root(self):
        """
        Root directory for the protocol
        """
        return self._root

    @property
    def script(self):
        """
        Script to run the protocol

        The script is either a program available in the search PATH or
        the path to a script. In the latter case, the path is ideally gave
        relative to the protocol root directory.

        The script is read from the matadata file if provided. Else, the
        default value defined in `meta_default.ini` is returned.
        """
        return self._meta['Protocol']['script']

    @property
    def log_directory(self):
        """
        Path to the directory where to store logs.
        """
        return self.root / pathlib.Path(self._meta['Protocol']['log_dir'])

    @property
    def stdout_path(self):
        """
        Path to the standard output log of the protocol execution.
        """
        return self.log_directory / path.Path('stdout.log')

    @property
    def stderr_path(self):
        """
        Path to the standard error log of the protocol execution.
        """
        return self.log_directory / path.Path('stderr.log')

    @property
    def exit_code_path(self):
        """
        Path to the file that records the exit code
        """
        return self.log_directory / pathlib.Path('EXIT_CODE')

    @property
    def exit_code(self):
        """
        Exit code for the protocol run.

        The exit code is an integer returned by the protocol script. It is
        assumed to be 0 if the script finished as expected. Non 0 values are
        expected to signal errors. If the protocol did not run yet, then the
        exit code is `None`.

        If the protocol was run by the current instance, then the exit code
        returned is the one saved as the run finished. Else, the exit code
        is read from the disk in the `EXIT_CODE` file.
        """
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

    @property
    def stdout(self):
        try:
            with open(str(self.stdout_path)) as infile:
                yield from infile
        except FileNotFoundError:
            raise ProtocolNotRunError()

    @property
    def stderr(self):
        try:
            with open(str(self.stderr_path)) as infile:
                yield from infile
        except FileNotFoundError:
            raise ProtocolNotRunError()


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
    Iterate over the Protocol instances for all the found protocols.
    """
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
    out_path = log_directory / pathlib.Path('stdout.log')
    err_path = log_directory / pathlib.Path('stderr.log')
    stdout = open(str(out_path), 'w')
    stderr = open(str(err_path), 'w')
    with stdout, stderr:
        process = subprocess.Popen(
            script,
            stdout=stdout,
            stderr=stderr,
            cwd=str(root.absolute()))
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
