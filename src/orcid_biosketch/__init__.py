"""Deprecated alias of :mod:`science_record_player` (renamed at ORCID's request, Nov 2026).

``import orcid_biosketch`` and ``import orcid_biosketch.<module>`` keep working and return
the very same module objects as ``science_record_player``; they will be removed in a future
release. Update imports to ``science_record_player``.
"""
import sys
import warnings

import science_record_player as _pkg

warnings.warn("orcid_biosketch was renamed science_record_player; the old name is deprecated",
              DeprecationWarning, stacklevel=2)
sys.modules[__name__] = _pkg
