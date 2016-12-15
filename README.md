# ALLATOM: A Library Leveraging Automated Testing Of Martini

Warning: This repository is under heavy development. It does not work yet!

## Directory structure

* src: source code of the ALLATOM main program
* library: library of function to factor common tasks in tests
* inputs: input files shared among the tests
* protocols: collection of tests

## Get ALLATOM

You can download the program using git:

```bash
git clone https://github.com/jbarnoud/ALLATOM.git
```

Or you can download a zip archive of the repository:
<https://github.com/jbarnoud/ALLATOM/archive/master.zip>

## Run ALLATOM

Run the `allatom` script with the destination directory. For instance, assuming
the current directory is the root of the repository:

```bash
./allatom ../destination
```

This will create  copy of the repository in `../destination` and run the test
protocol in that copied directory.

You can also provide a list of directories containing replacement input files
or additional protocols:

```bash
./allatom \
    -i ../alternative-inputs1 \
    -i ../alternative-inputs2 \
    -p ../additional-protocols \
    ../destination
```

The `inputs` directory of the repository contains the input files shared by the
test protocols. These files can be the force field definition, basic MDP
parameters or some molecule topologies. As everything in the repository, the
`inputs` directory is copied in the destination directory. When directories are
provided with the `-i` option, they are overlayed on top of the `inputs`
directory from the repository in the destination.

The test protocols are stored in the `protocols` directory. The `-p` option
allows to overlay user provided protocol directories.

## Write a test protocol

A test protocol is a directory containing a script to execute and a metadata
file.

### Protocol script

The protocol script is a python or bash script—or any other script actually.
The script will be executed by the ALLATOM main program and its output will be
analyzed to write a report.

The script is expected to exit with a zero exit code if the script encounter no
error, and a non-zero code if any it encountered any error. If the exit code is
non-zero, the protocol will be reported as having had an error.

The script should also write a success in the `SUCCESS_CODE` file. The success
code is a integer with a zero value if the test succeeded and the resulting
values match with the atomistic or experimental reference. It is a non-zero is
the result does not match. By default the `SUCCESS_CODE` file is expected to be
in `./LOGS/SUCCESS_CODE`, yet the path may be changed in the metadata file. The
path to the `SUCCESS_CODE` file is provided in the `AA_SUCCESS_CODE`
environment variable.

The ALLATOM main program sets up environment variables for the scripts to adapt
to the testing environment:
* `AA_INPUTS` is the path to the shared inputs directory;
* `AA_SUCCESS_CODE` is the path to the file recording the success code of the
  protocol script;
* `AA_LOG_DIR` is the path to the directory where the logs for the protocol
  will be kept.
