"""Deprecated alias of :mod:`science_record_player.network`."""
import sys

import orcid_biosketch  # noqa: F401  (emits the deprecation warning once)
from science_record_player import network as _module

if __name__ == "__main__":  # python -m orcid_biosketch.network
    raise SystemExit(_module.main())

sys.modules[__name__] = _module
