import os
import csv
import datetime

from git import Repo

gitpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lock_repo = Repo(gitpath)

def get_lockfile_path(pkg):
    return os.path.join(gitpath, 'repos', pkg, 'locks.txt')

def build_lock_file(pkg, path):
    """
    Build a text file with a list of all of the files in a package with no locks
    """
    from git import Repo
    import errno
    repo = Repo(path)
    lock_time = str(datetime.datetime.now())
    files = ['"{0}" "{1}" "{2}"'.format(f.path, "None", lock_time) for f in repo.tree().traverse()]
    
    # Create the package if it does not exist
    try:
        os.makedirs(os.path.join(gitpath, 'repos', pkg))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    # Write the files
    lockfile = get_lockfile_path(pkg)
    with open(lockfile, 'w+') as f:
        f.write("\n".join(files))

def get_all_locks(pkg=None, lock_tree=None):
    """
    Load all the locks for a file
    """
    import csv
    if lock_tree is None:
        if pkg is None:
            raise Exception("You must either enter a valid pkg or lock_tree")
        else:
            lock_tree = get_lockfile_path(pkg)

    with open(lock_tree, 'r') as f:
        locks = [row for row in csv.reader(f, delimiter=" ", quotechar='"')]

    lock_files, lock_users, lock_times = list(zip(*locks))
    return lock_files, lock_users, lock_times

def get_locked_info(pkg=None, lock_tree=None, sortby=None, username=None):
    """
    Load the files, users, and times for all the files that are locked
    """
    lock_files, lock_users, lock_times = get_all_locks(pkg, lock_tree)
    if username is None:
        lock_indices = [n for n in range(len(lock_users)) if lock_users[n]!="None"]
    else:
        lock_indices = [n for n in range(len(lock_users)) if lock_users[n]==username]

    locked_files = [lock_files[n] for n in lock_indices]
    locked_users = [lock_users[n] for n in lock_indices]
    locked_times = [lock_times[n] for n in lock_indices]
    
    if sortby is not None or username is not None:
        if sortby == 'user':
            import numpy as np
            locked_array = np.array([locked_files, locked_times])
            user_array = np.array([locked_users])
            
            for user in np.unique(locked_users):
                print("Files locked by {0}".format(username))
                print('\n'.join(locked_array[user_array==user]))
        elif username is not None:
            print("Files locked by {0}".format(username))
            print('\n'.join([' '.join(x) for x in list(zip(locked_files, locked_times))]))
        else:
            raise ValueError("sortby parameter {0} is not yet supported".format(sortby))
        
    return locked_files, locked_users, locked_times

def get_username(username):
    """
    If a username is not specified, use the global user.name from ~/.gitconfig
    """
    from git.config import GitConfigParser
    if username is None:
        gitconfig_name = os.path.expanduser('~/.gitconfig')
        if not os.path.isfile(gitconfig_name):
            raise ValueError("You must enter a username if you do not have a ~/.gitconfig file")
        gitconfig = GitConfigParser(gitconfig_name, read_only=True)
        username = gitconfig.get('user','name')
        if username == '':
            raise ValueError("Could not load user.name from ~/.gitconfig")
    return username

def save_lock_file(filename, pkg, username, idx):
    """
    Save a modified file's locked permission
    """
    # Open the entire lock file
    lock_tree = get_lockfile_path(pkg)
    with open(lock_tree, 'r') as f:
        files = f.readlines()
    # Replace the selected file entry with a lock
    lock_time = str(datetime.datetime.now())
    files[idx] = '"' + '" "'.join([filename, username, lock_time]) + '"\n'
    #Re-write the lock file
    with open(lock_tree, 'w+') as f:
        f.write("".join(files))
    return True

def lock_file(filename, pkg, username=None, pwd=None):
    """
    Attempt to lock a file
    """
    got_lock = False
    username = get_username(username)
    lock_files, lock_users, lock_times = get_all_locks(pkg)
    try:
        idx = lock_files.index(filename)
    except ValueError as e:
        raise Exception("Could not find {0} in the lock file".format(filename))
    
    if lock_users[idx]!="None":
        if lock_users[idx]==username:
            print("You have had '{0}' locked since {1}".format(filename, lock_times[idx]))
        else:
            print("Unable to get lock, '{0}' is currently locked by {1} since {2}".format(filename, 
                                                                                          lock_users[idx],
                                                                                          lock_times[idx]))
    else:
        if save_lock_file(filename, pkg, username, idx):
            got_lock = True
            print("Successfully locked {0}".format(filename))
    return got_lock

def unlock_file(filename, pkg, username=None, pwd=None):
    """
    Unlock a file, if the file is locked by the current user
    """
    username = get_username(username)
    lock_files, lock_users, lock_times = get_all_locks(pkg)
    try:
        idx = lock_files.index(filename)
    except ValueError as e:
        raise Exception("Could not find {0} in the lock file".format(filename))
    
    if username!=lock_users[idx]:
        if lock_users[idx]=="None":
            print("'{0}' is already unlocked")
        else:
            print("You do not have a lock on {0}, it is currently locked by {1}".format(filename,
                                                                                        lock_users[idx]))
    else:
        save_lock_file(filename, pkg, "None", idx)
        print("'{0}' has successfully been unlocked".format(filename))
    return True

#input from user
pkg = 'afw'
repo_path = '/Users/fred/LSST/afw'

build_lock_file(pkg, repo_path)
lock_file('python/lsst/afw/geom/coordinateBase.cc', 'afw')

lock_file('include/lsst/afw/table/io/FitsReader.h', 'afw', 'fred')
lock_file('include/lsst/afw/table/io/FitsSchemaInputMapper.h', 'afw', 'cyndi')
lock_file('include/lsst/afw/table/io/FitsWriter.h', 'afw', 'sophie')
lock_file('include/lsst/afw/table/io/InputArchive.h', 'afw', 'fred')

lock_file('python/lsst/afw/geom/coordinateBase.cc', 'afw')
lock_file('include/lsst/afw/table/io/FitsReader.h', 'afw')
lock_file('include/lsst/afw/table/io/FitsSchemaInputMapper.h', 'afw')
lock_file('include/lsst/afw/table/io/FitsWriter.h', 'afw')
lock_file('include/lsst/afw/table/io/InputArchive.h', 'afw')

#unlock_file('include/lsst/afw/table/io/InputArchive.h', 'afw')
#unlock_file('include/lsst/afw/table/io/InputArchive.h', 'afw', 'fred')

get_locked_info(pkg, sortby='user')
#get_locked_info(pkg, username="fred")