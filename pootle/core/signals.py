#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import Signal


changed = Signal(
    use_caching=True)
config_updated = Signal(
    use_caching=True)
create = Signal(
    use_caching=True)
delete = Signal(
    use_caching=True)
update = Signal(
    use_caching=True)
update_checks = Signal(
    use_caching=True)
update_data = Signal(use_caching=True)
update_revisions = Signal(use_caching=True)
filetypes_changed = Signal(
    use_caching=True)
update_scores = Signal(
    use_caching=True)
toggle = Signal(
    use_caching=True)
