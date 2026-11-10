"""Deprecated alias of :mod:`science_record_player.playground`."""
import sys

import orcid_biosketch  # noqa: F401  (emits the deprecation warning once)
from science_record_player import playground as _module

sys.modules[__name__] = _module
