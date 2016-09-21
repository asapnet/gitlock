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