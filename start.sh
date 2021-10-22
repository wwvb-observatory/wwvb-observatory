#!/bin/bash
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

cd "$(dirname "$0")"
exec screen -d -m -c screenrc -S wwvb-observatory
