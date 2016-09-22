import git
import logging
from git.remote import FetchInfo
from git.remote import PushInfo

logger = logging.getLogger('gitlock.git_io')

class GitError(Exception):
    pass

def pull(repo):
    """
    Attempt to pull changes from the remote master
    """
    origin = repo.remote('origin')
    pull_result = origin.pull()[0]

    if pull_result.flags&FetchInfo.ERROR:
        print("There was an unknown error pulling from the remote. "
              "This is likely an unexpected merge conflict. "
              "Entering ipython console for debugging purposes")
        import IPython; IPython.embed()
        raise GitError("There was an error pulling the data from the remote origin")

    if pull_result.flags&FetchInfo.HEAD_UPTODATE:
        logger.info("Lock file is already up to date\n")
    elif pull_result.flags&FetchInfo.FAST_FORWARD:
        logger.info("Updates pulled from remote")
    else:
        print("There was an unknown flag while pulling from the remote")
        import IPython; IPython.embed()
    return True

def update_remote(commit_msg, lockfile_path, repo=None, repo_path=None):
    """
    Attempt to commit a lock and push it to the remote master. If this fails, rewind to the
    lockfile before the commit.
    """
    if repo is None:
        if repo_path is None:
            return GitError("Either a repo or path to a repo is required")
        repo = git.Repo(path)

    try:
        # Stage the lockfile
        repo.git.add(lockfile_path)
    except:
        return GitError("Error staging lockfile")
    try:
        # Commit changes to the lockfile
        repo.index.commit(commit_msg)
    except:
        # If an error occured before a commit was made, make sure to reset the lockfile
        repo.git.reset(lockfile_path)
        return GitError("Error commiting lockfile to local repo")

    try:
        # Attempt to push the changes to the remote
        origin = repo.remote('origin')
        push_result = origin.push()[0]
        
        if push_result.flags&PushInfo.ERROR:
            logger.error("Push flags: {0}".push_result.flags)
            raise GitError('Unknown Error in push')
        elif push_result.flags&PushInfo.FAST_FORWARD:
            logger.info("Push successful")
        else:
            print("Not sure what happened during push, don't forget to set success=True if it is")
            print('Push flags: {0}'.push_result.flags)
    except:
        print('error in push!!!')
        import IPython; IPython.embed()
        # Rewind the last commit
        repo.git.reset('--hard', 'HEAD~1')
    return None