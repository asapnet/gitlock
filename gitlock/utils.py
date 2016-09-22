import os
from collections import OrderedDict
import errno

def get_full_path(path):
    """
    If a ~ is present in the path, expand it. Return the absolute path to a (potentially) relative path.
    """
    if path is None:
        return None
    return os.path.abspath(os.path.expanduser(path))

def create_path(path):
    """
    Create the path if it does not exist. 
    If a new file or directory was created return True, otherwise return false
    """
    try:
        os.makedirs(get_full_path(path))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        return False
    return True

def check_required(args, required):
    """
    Make sure all of the required arguments are present
    """
    missing = []
    for arg in required:
        if getattr(args, arg) is None:
            missing.append(arg)
    if len(missing)>0:
        raise ValueError("You are missing required arguments for {0}".format(missing))

def get_gitpath(gitpath):
    if gitpath is None:
        gitlock_cfg_path = get_gitlock_cfg_path()
        gitlock_config = load_config(gitlock_cfg_path)
        gitpath = gitlock_config['gitpath']
    gitpath = get_full_path(gitpath)
    return gitpath

def get_gitlock_cfg_path():
    """
    Location of the gitlock configuration file
    """
    return get_full_path(os.path.join('~', '.gitlock', 'gitlock.cfg'))

def get_config_path(gitpath, pkg):
    """
    Load the path to a configuration file
    """
    return get_full_path(os.path.join(gitpath, 'repos', pkg, 'locks.cfg'))

def get_lockfile_path(gitpath, pkg):
    """
    Load the path to a lockfile
    """
    return get_full_path(os.path.join(gitpath, 'repos', pkg, 'locks.txt'))

def load_config(path):
    """
    Load a configuration file
    """
    import yaml
    with open(path, 'r') as file:
        config = yaml.load(file)
    return config

def edit_git_cfg(gitpath, user):
    """
    Create or edit the gitlock configuration file
    """
    import yaml
    config_path = get_gitlock_cfg_path()
    create_path(os.path.dirname(config_path))
    if os.path.isfile(config_path):
        config = load_config(config_path)
    else:
        config = OrderedDict()
    
    # Update any config fields that have been specified
    config['gitpath'] = get_full_path(gitpath)
    if user is not None:
        config['user'] = user
    with open(config_path, 'w+') as stream:
        yaml.dump(config, stream)
    return config

def edit_lock_cfg(pkg, gitpath=None, pkg_path=None, user=None):
    """
    Create or edit a package configuration file
    """
    import yaml
    
    gitpath = get_gitpath(gitpath)
    config_path = get_config_path(gitpath, pkg)
    create_path(os.path.dirname(config_path))
    if os.path.isfile(config_path):
        config = load_config(config_path)
    else:
        config = OrderedDict()
    
    # Update any config fields that have been specified
    config['pkg'] = pkg
    if pkg_path is not None:
        config['pkg_path'] = get_full_path(pkg_path)
    if user is not None:
        config['user'] = user
    with open(config_path, 'w+') as stream:
        yaml.dump(config, stream)
    return config

def create_lockfile(gitpath, pkg, pkg_path, overwrite=False, update=False):
    """
    Build a text file with a list of all of the files in a package with no locks
    """
    import git
    import datetime
    import gitlock.lock
    
    gitpath = get_gitpath(gitpath)
    if pkg_path is None:
        config_path = get_config_path(gitpath, pkg)
        config = load_config(config_path)
        pkg_path = config['pkg_path']
    
    git_repo = git.Repo(pkg_path)
    lock_time = str(datetime.datetime.now())
    files = ['"{0}" "{1}" "{2}"'.format(f.path, "None", lock_time) for f in git_repo.tree().traverse()]

    # Create the package if it does not exist
    lockfile_path = get_lockfile_path(gitpath, pkg)
    if os.path.isfile(lockfile_path) and not overwrite and not update:
        print("The lockfile already exists for {0}".format(pkg))
    else:
        repo = gitlock.lock.Repo(pkg, gitpath)
        if os.path.isfile(lockfile_path) and update:
            locks = repo.get_locked_info(display=False)
            for filename, lock in locks.items():
                entry = '"' + '" "'.join([lock.filename, lock.user, lock.time]) + '"'
                idx = [n for n,f in enumerate(files) if f.startswith('"'+filename+'"')]
                if len(idx)==1:
                    files[idx[0]] = entry
                elif len(idx)==0:
                    files.append(entry)
                else:
                    raise Exception("Multiple entries for {0}".format(filename))
            commit_msg = "Update lockfile"
        else:
            commit_msg = "Rebuild lockfile"
            create_path(os.path.dirname(lockfile_path))
            locks = None
        # Backup the lockfile
        new_file = True
        if os.path.isfile(lockfile_path):
            new_file = False
            with open(lockfile_path, 'r') as f:
                old_files = f.readlines()
        # Write the lockfile
        with open(lockfile_path, 'w+') as f:
            f.write("\n".join(files))
        print('finished writing', lockfile_path)
        
        # Attempt to push the changes to the remote
        error = gitlock.git_io.update_remote(commit_msg, lockfile_path, repo.lock_repo)
        if error is not None and not new_file:
            # Resore the lockfile if there was an error while saving
            print("Restoring lockfile")
            with open(lockfile_path, 'w+') as f:
                f.write("".join(old_files))
            raise error
        