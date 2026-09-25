"""Visa types supported by the flow; see base.VisaProfile.

To add a visa type: create a module with a ``@register``-ed VisaProfile
subclass, import it below, add its UPLOAD_CONFIG / UPLOAD_FILE_CODE_BY_VISA_TYPE
entries in constants.py and a case in tests/test_flow_snapshots.py.
"""

from .base import (
    ReuseRule,
    UploadItem,
    VisaProfile,
    get_visa_profile,
    normalize_visa_type,
    registered_visa_types,
)

# Imported after .base: the profile modules import flows.*, which imports
# visa_types.base back while this package is still initialising.
from . import business, family, study, tourism  # noqa: E402,F401  (registers profiles)

__all__ = [
    "ReuseRule",
    "UploadItem",
    "VisaProfile",
    "get_visa_profile",
    "normalize_visa_type",
    "registered_visa_types",
]
