import os
import csv
import datetime
from collections import OrderedDict

import git

import gitlock.utils as utils
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


class Repo(object):
    def __init__(self, pkg, gitpath=None):
        """
        Initialize a repo with a gitlock for a specific package
        """
        self.gitpath = utils.get_gitpath(gitpath)
        self.lock_repo = git.Repo(self.gitpath)
        self.pkg = pkg
        self.locks = OrderedDict()
        self.lockfile_path = utils.get_lockfile_path(self.gitpath, self.pkg)
        config_path = utils.get_config_path(self.gitpath, self.pkg)
        self.config = utils.load_config(config_path)

    def update_all_locks(self):
        """
        Pull changes to the lock file from the remote repository and update the local lockfile
        """
        import csv
        if not gitlock.git_io.pull(self.lock_repo):
            raise gitlock.git_io.GitError("There was an error pulling the data from the remote origin")
        with open(self.lockfile_path, 'r') as f:
            self.locks = OrderedDict([(row[0],Lock(self, *row)) 
                                    for row in csv.reader(f, delimiter=" ", quotechar='"')])

        return self.locks

    def get_locked_info(self, username=None, sortby='user', display=True):
        """
        Load the information about the currently locked files
        """
        self.update_all_locks()
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
                    print("{0}'s locked files:".format(user))
                    print('\n'.join(['\t{0}: at {1}'.format(lock.filename, lock.time) for filename, lock 
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
            if lock.locked:
                if lock.user==username:
                    print("You have had '{0}' locked since {1}".format(filename, lock.time))
                else:
                    print("Unable to get lock, '{0}' is currently locked by {1} since {2}".format(
                          filename, lock.user, lock.time))
            else:
                lock.user = username
                commit_msg = 'lock {0} by {1}'.format(filename, username)
                got_lock = self.save_lockfile(lock, commit_msg)
                print("Successfully locked {0}".format(filename))
        return got_lock

    def save_lockfile(self, lock, commit_msg):
        """
        Save a modified file's locked permission
        """
        idx = list(self.locks.keys()).index(lock.filename)
        with open(self.lockfile_path, 'r') as f:
            files = f.readlines()
        old_files = files[:]
        # Replace the selected file entry with a lock
        lock.time = str(datetime.datetime.now())
        files[idx] = '"' + '" "'.join([lock.filename, lock.user, lock.time]) + '"\n'
        #Re-write the lock file
        with open(self.lockfile_path, 'w+') as f:
            f.write("".join(files))
        # Attempt to push the changes to the remote
        error = gitlock.git_io.update_remote(commit_msg, self.lockfile_path, self.lock_repo)
        if error is not None:
            # Resore the lockfile if there was an error while saving
            print("Restoring lockfile")
            with open(self.lockfile_path, 'w+') as f:
                f.write("".join(old_files))
            raise error
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
            if lock.locked:
                print("You do not have a lock on {0}, it is currently locked by {1}".format(filename,
                                                                                            lock.user))
            else:
                print("'{0}' is already unlocked")
        else:
            lock.user = "None"
            commit_msg = "unlock {0} by {1}".format(filename, username)
            unlocked = self.save_lockfile(lock, commit_msg)
            print("'{0}' has successfully been unlocked".format(filename))
        return unlocked

