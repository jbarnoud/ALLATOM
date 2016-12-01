# ALLATOM: A Library Leveraging Automated Testing Of Martini

Warning: This repository is under heavy development. It does not work yet!

## Directory structure

* src: source code of the ALLATOM main program
* library: library of function to factor common tasks in tests
* inputs: input files shared among the tests
* protocols: collection of tests 

## What happens when we run the main program?

1. A copy of the ALLATOM directory is made, and the user structure is applied on top of it. This would be a good use of specialized file systems such as overlayfs or unionfs, yet using these files systems makes us very dependant on the user's configuration.
2. The sanity of the resulting file tree is tested. Are all the needed file available? Are all the dependencies accessible? These tests allow to fail as early as possible if anything is missing.
3. The run environment is setup. This mostly means setting up the environment variable for gromacs and other programs, and loading a virtualenv.
4. List the tests in the `protocols` directory. Select the ones that fit the user's selection criteria.
