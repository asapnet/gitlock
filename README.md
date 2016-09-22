# gitlock

This repository is for putting soft locks on files in a github repo that multiple people are working on. This was primarily developed for the pybind11 port where multiple people will be touching multiple header files at any given time. While constant rebasing with the main ticket branch is still necessary, without some way to communicate which files are under current development this could quickly get out of hand.

## Installation

This repo must be cloned on the local machine to work. 
```
user@mycpu:~/lsst$ git clone https://github.com/lsst-dm/gitlock.git gitlock
```

From the main gitlock repo directory (for the example above `/User/user/lsst/gitlock`) type
```
user@mycpu:~/lsst/gitlock$ python setup.py install
```

This will install the gitlock package and a ``gitlock`` command line script.

# Quick Start

## Initializing the locking repo

Assuming that you are in the directory `~/lsst/gitlock` and you want to put locks on the `afw` repo in `~/lsst/afw`, the package can be initialized using
```
user@mycpu:~/lsst/gitlock$ gitlock init afw -g . -p ../afw
```
or more generally
```
user@mycpu:~/lsst/gitlock$ gitlock init afw -g <gitpath> -p <pkg_path>
```

The "-g" is used to specify the path to the gitlock repo (gitpath). The "-p" is used to specify the path to the repo that is being developed (in this case afw). These can either be relative or absolute paths.

The init command also builds a lockfile that contains a list of all of the files in the repository (in this case afw). Since there is already an afw filelock created for the repo, the above command will output `The lockfile already exists for afw`.

Note: If you do not have a ~/.gitconfig file that contains your git username you will either need to create one or add a `-u <username>` option to the gitlock init command. This is the username that will be used to lock and unlock your files.

## Viewing current locks

You can get a list of all the currently locked files, sorted by user, with the command
```
gitlock info <packagename>
```
where <packagename> is afw for the above examples. If you want to only see the files locked by a specific user (for example yourself) use
```
gitlock info <packagename> -u <username>
```

## Locking a file

To lock a file use the command 
```
gitlock lock <packagename> -f <filename>
```

This is typically run from inside a repo, so <filename> can either be the name of a file in the current working directory, the relative path to a file, or the absolute path to a file. For example
```
user@mycpu:~/lsst/afw/python/lsst/afw/table$ gitlock lock afw -f __init__.py
```
and
```
user@mycpu:~/lsst/afw$ gitlock lock afw -f python/lsst/afw/table/__init__.py
```
both attempt to lock the same file. You will be notified if the lock was successfull or if someone else has a lock on the file.

## Unlocking a file

If you have a lock on a file you can unlock it using the command
```
gitlock unlock <packagename> -f <filename>
```
You can only unlock files that are currently locked by you. This can be overridden by specifying a `-u <username>` in the lock or unlock commands but should only be used if you have been in contact with the person who currently has the lock (for example, they left for the weekend and forgot to unlock the file).

## Updating the lockfile

If new files are added to the repoistory it might be necessary to update the lockfile. This has been tested and should work but it is recommended that users do not typically perform updates themselves for the time being. If it is necessary to update the lockfile use the command

```
gitlock update <packagename>
```

This will create a new lockfile from scratch, deleting any deleted files, then relock the files that currently have locks. Any locked files removed from the repository will be re-added to the lock file.

## Rebuilding

It may be necessary to do a rebuild and clear all of the locks for some catastrophic reason. In that case run
```
gitlock build afw -o True
```
to overwrite the current lockfile. This will remove *ALL* locks, so be sure that this is what you mean to do.

# A Note about Catastrophic failure

If something very unexpected happens, like a failure to push to or pull from the remote repo, you will likely be dropped into an ipython console. You can either `exit` out of the terminal or if you're feeling froggy, attempt to debug the available variables to discover what went wrong.

In general most failures should be properly accounted for and raise expected Exceptions.
