import git

def pull(path):
    repo = git.Repo(path)
    origin = repo.remote('origin')
    