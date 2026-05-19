from importlib import metadata


__version__ = "0.3.3"


def get_version():
    try:
        return metadata.version("wecom-bot-svr")
    except metadata.PackageNotFoundError:
        return __version__
