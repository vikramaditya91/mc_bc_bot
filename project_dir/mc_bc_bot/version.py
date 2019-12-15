VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_EXTRA = 'a0'

__version__ = "{}.{}.{}".format(VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
__loose_version__ = "{}.{}".format(VERSION_MAJOR, VERSION_MINOR)

if VERSION_EXTRA:
    __version__ = "{}-{}".format(__version__, VERSION_EXTRA)
    __loose_version__ = "{}-{}".format(__loose_version__, VERSION_EXTRA)
    __version_info__ = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, float('inf'))
else:
    __version_info__ = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)


__all__ = ['{}'.format(__version__), '{}'.format(__version_info__), '{}'.format(__loose_version__)]
