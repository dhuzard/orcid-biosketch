"""Deprecated alias of :mod:`science_record_player.cli`."""
import sys

import orcid_biosketch  # noqa: F401  (emits the deprecation warning once)
from science_record_player import cli as _module

if __name__ == "__main__":  # python -m orcid_biosketch.cli
    raise SystemExit(_module.main())

sys.modules[__name__] = _module
