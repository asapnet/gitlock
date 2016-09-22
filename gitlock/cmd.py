import os
import logging
import argparse

import gitlock.utils as utils
import gitlock.lock

logger = logging.getLogger('gitlock')

def lock(args):
    """
    Attempt to lock a file
    """
    utils.check_required(args, ['pkg', 'filename'])
    repo = gitlock.lock.Repo(args.pkg, args.gitpath)
    filename = os.path.join(os.getcwd(), args.filename)
    filename = os.path.relpath(filename, repo.config['pkg_path'])
    repo.lock(filename, args.user)

def unlock(args):
    """
    Attempt to unlock a file
    """
    utils.check_required(args, ['pkg', 'filename'])
    repo = gitlock.lock.Repo(args.pkg, args.gitpath)
    filename = os.path.join(os.getcwd(), args.filename)
    filename = os.path.relpath(filename, repo.config['pkg_path'])
    repo.unlock(filename, args.user)

def get_info(args):
    """
    Get the information about all of the locked files. If a user is specified, only
    get information about that users locked files
    """
    utils.check_required(args, ['pkg'])
    repo = gitlock.lock.Repo(args.pkg, args.gitpath)
    repo.get_locked_info(username=args.user, sortby=args.sortby, display=True)

def init(args):
    """
    Create the gitlock configuration file, package configuration file, and build the
    lockfile (or overwrite it if it exists and overwrite is True).
    """
    utils.check_required(args, ['gitpath', 'pkg', 'pkg_path'])
    utils.edit_git_cfg(args.gitpath, args.user)
    utils.edit_lock_cfg(args.pkg, args.gitpath, args.pkg_path, args.user)
    utils.create_lockfile(args.gitpath, args.pkg, args.pkg_path, args.overwrite, update=False)

def cfg(args):
    """
    Edit the package configuration file
    """
    utils.check_required(args, ['pkg'])
    utils.edit_lock_cfg(args.pkg, args.gitpath, args.pkg_path, args.user)

def gitcfg(args):
    """
    Edit the gitlock configuration file
    """
    utils.check_required(args, ['gitpath'])
    utils.edit_git_cfg(args.gitpath, args.user)

def build(args):
    """
    Build the lockfile
    """
    utils.check_required(args, ['pkg'])
    utils.create_lockfile(args.gitpath, args.pkg, args.pkg_path, args.overwrite, update=False)

def update(args):
    """
    Update the lockfile
    """
    utils.check_required(args, ['pkg'])
    utils.create_lockfile(args.gitpath, args.pkg, args.pkg_path, overwrite=False, update=True)

commands = {
    'lock': lock,
    'unlock': unlock,
    'info': get_info,
    'init': init,
    'cfg': cfg,
    'gitcfg': gitcfg,
    'build': build,
    'update': update
}

def main():
    parser = argparse.ArgumentParser(description="Commands for locking git files")
    parser.add_argument("command", type=str, 
                        help="Command to run (from {0})".format(list(commands.keys())))
    parser.add_argument('pkg', type=str,
                        help="Name of the package")
    parser.add_argument('-u', '--user', type=str, default=None,
                        help="github ID of the user")
    parser.add_argument('-g', '--gitpath', default=None,
                        help="Path to gitlock repo")
    parser.add_argument('-p','--pkg_path', type=str, default=None,
                        help="Path to git repo for the package")
    parser.add_argument('-o','--overwrite', type=bool, default=False,
                        help="Overwrite an existing lockfile (for command='build')")
    parser.add_argument('-l','--logging', type=str, default='info',
                        help="Logging level")
    parser.add_argument('-s','--sortby', type=str, default='user',
                        help="Sorting order for displaying gitlock info")
    parser.add_argument('-f','--filename', type=str, default=None,
                        help="Filename to lock or unlock")
    #parser.add_argument('','', type=str, default=None,
    #                    help="")
    args = parser.parse_args()

    # Set the logging level
    log_level = getattr(logging, args.logging.upper())
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    logger.setLevel(log_level)
    logger.addHandler(ch)

    # Execute the command
    if args.command not in commands:
        raise ValueError("Valid commands are {0}".format(commands.keys()))
    commands[args.command](args)