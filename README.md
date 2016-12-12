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
