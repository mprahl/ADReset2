# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import logging
import pkg_resources


log = logging.getLogger('adreset')

try:
    version = pkg_resources.get_distribution('adreset').version
except pkg_resources.DistributionNotFound:
    version = 'unknown'
