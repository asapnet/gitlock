import os
from distutils.core import setup

repo_data = []
for root, dirs, files in os.walk('repos'):
    if len(files)>0:
        repo_data += [os.path.join(root, f) for f in files if f.endswith('.txt')]

packages = []
for root, dirs, files in os.walk('.'):
    if root.startswith('./.'):
        continue
    if not root.startswith('./build') and '__init__.py' in files:
        packages.append(root[2:])

pkg_data = {'gitlock': repo_data}

print(packages)
print(pkg_data)

setup(name='gitlock',
      version='0.0.1',
      description='File lock for git',
      url='http://github.com/fred3m/gitlock',
      author='Fred Moolekamp',
      author_email='fred.moolekamp@gmail.com',
      license='MIT',
      packages=packages,
      package_data=pkg_data,
      scripts=['scripts/gitlock']
      )
