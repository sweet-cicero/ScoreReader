"""ScoreReader reads the pages of a choir score on this computer, by rules on the ink of the page."""
import os


def setting(name: str, default=None):
    """A setting from the environment: SCOREREADER_<name>, or `default` when it is not set. The package was named
    scoreread before, so a setting under its old name (SCOREREAD_<name>) still counts where the new one is not set."""
    return os.environ.get('SCOREREADER_' + name, os.environ.get('SCOREREAD_' + name, default))
