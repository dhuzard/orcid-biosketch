"""Deprecated alias of :mod:`science_record_player.collaboration`."""
import sys

import orcid_biosketch  # noqa: F401  (emits the deprecation warning once)
from science_record_player import collaboration as _module

sys.modules[__name__] = _module
