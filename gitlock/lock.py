import os
import csv
import datetime
from collections import OrderedDict

import git

import gitlock.git_io

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


class Lock(object):
    def __init__(self, repo, filename, user, time):
        self.filename = filename
        self.user = user
        self.time = time
        self.locked = user != 'None'
    
    def lock(user):
        self.user = user
        self.locked = user != 'None'

    def unlock(self):
        pass


class Repo(object):
    def __init__(self, pkg, pkg_path=None, gitpath=None):
        """
        Initialize a repo with a gitlock for a specific package
        """
        if gitpath is None:
            gitpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.gitpath = gitpath
        self.lock_repo = git.Repo(gitpath)
        self.pkg = pkg
        self.pkg_path = pkg_path
        self.locks = OrderedDict()
        self.lockfile_path = os.path.join(self.gitpath, 'repos', self.pkg, 'locks.txt')
    
    def build_lockfile(pkg, path=None, overwrite=False, push_to_remote=True):
        """
        Build a text file with a list of all of the files in a package with no locks
        """
        import errno
        
        if path is None:
            if self.pkg_path is None:
                raise ValueError("You must specify a path or repo.pkg_path")
            path = self.pkg_path

        repo = git.Repo(path)
        lock_time = str(datetime.datetime.now())
        files = ['"{0}" "{1}" "{2}"'.format(f.path, "None", lock_time) for f in repo.tree().traverse()]
    
        # Create the package if it does not exist
        try:
            os.makedirs(os.path.join(gitpath, 'repos', pkg))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            if not overwrite:
                print("File already exists. Use 'overwrite=False' to create a blank lock file")
                return
        # Write the files
        lockfile = get_lockfile_path(pkg)
        with open(lockfile, 'w+') as f:
            f.write("\n".join(files))

    def update_all_locks(self):
        """
        Pull changes to the lock file from the remote repository and update the local lockfile
        """
        import csv
        #gitio.pull()
        with open(self.lockfile_path, 'r') as f:
            self.locks = OrderedDict([(row[0],Lock(self, *row)) 
                                    for row in csv.reader(f, delimiter=" ", quotechar='"')])

        return self.locks

    def get_locked_info(self, username=None, sortby='user', display=True):
        """
        Load the information about the currently locked files
        """
        if username is None:
            locks = OrderedDict([(filename, lock) for filename, lock in self.locks.items() 
                                        if lock.user!="None"])
        else:
            locks = OrderedDict([(filename, lock) for filename, lock in self.locks.items() 
                                        if lock.user==username])

        if display:
            if sortby == 'user':
                if username is None:
                    users = list(set([lock.user for filename, lock in locks.items()]))
                else:
                    users = [username]
                for user in users:
                    print("Files locked by {0}".format(user))
                    print('\n'.join(['{0}: at {1}'.format(lock.filename, lock.time) for filename, lock 
                                     in locks.items() if lock.user==user]))
            else:
                raise ValueError("sortby parameter {0} is not yet supported".format(sortby))

        return locks

    def lock(self, filename, username=None):
        """
        Attempt to lock a file
        """
        got_lock = False
        username = get_username(username)
        locks = self.update_all_locks()
        if filename not in locks:
            print("Could not find {0} in the lock file. "
                  "The the filename or add it to lockfiles".format(filename))
        else:
            lock = locks[filename]
            if lock.user!='None':
                if lock.user==username:
                    print("You have had '{0}' locked since {1}".format(filename, lock.time))
                else:
                    print("Unable to get lock, '{0}' is currently locked by {1} since {2}".format(
                          filename, lock.user, lock.time))
            else:
                lock.user = username
                got_lock = self.save_lockfile(lock)
                print("Successfully locked {0}".format(filename))
        return got_lock

    def save_lockfile(self, lock):
        """
        Save a modified file's locked permission
        """
        idx = list(self.locks.keys()).index(lock.filename)
        with open(self.lockfile_path, 'r') as f:
            files = f.readlines()
        # Replace the selected file entry with a lock
        lock.time = str(datetime.datetime.now())
        files[idx] = '"' + '" "'.join([lock.filename, lock.user, lock.time]) + '"\n'
        #Re-write the lock file
        with open(self.lockfile_path, 'w+') as f:
            f.write("".join(files))
        return True

    def unlock(self, filename, username=None):
        """
        Unlock a file, if the file is locked by the current user
        """
        unlocked = False
        username = get_username(username)
        locks = self.update_all_locks()
        if filename not in locks:
            raise Exception("Could not find {0} in the lock file".format(filename))

        lock = locks[filename]
        if username!=lock.user:
            if lock.user=="None":
                print("'{0}' is already unlocked")
            else:
                print("You do not have a lock on {0}, it is currently locked by {1}".format(filename,
                                                                                            lock.user))
        else:
            lock.user = "None"
            unlocked = self.save_lockfile(lock)
            print("'{0}' has successfully been unlocked".format(filename))
        return unlocked

