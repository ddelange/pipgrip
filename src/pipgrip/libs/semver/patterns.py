# BSD 3-Clause License
#
# Copyright (c) 2020 - 2024, ddelange, <ddelange@delange.dev>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# SPDX-License-Identifier: BSD-3-Clause
import re

MODIFIERS = (
    "[._-]?"
    r"((?!post)(?:beta|b|c|pre|RC|alpha|a|patch|pl|p|dev)(?:(?:[.-]?\d+)*)?)?"
    r"([+-]?([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?"
)

_COMPLETE_VERSION = (
    r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?{}(?:\+[^\s]+)?".format(MODIFIERS)
)

COMPLETE_VERSION = re.compile("(?i)" + _COMPLETE_VERSION)

CARET_CONSTRAINT = re.compile(r"(?i)^\^({})$".format(_COMPLETE_VERSION))
TILDE_CONSTRAINT = re.compile("(?i)^~(?!=)({})$".format(_COMPLETE_VERSION))
TILDE_PEP440_CONSTRAINT = re.compile("(?i)^~=({})$".format(_COMPLETE_VERSION))
X_CONSTRAINT = re.compile(r"^(!=|==)?\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.[xX*])+$")
BASIC_CONSTRAINT = re.compile(
    r"(?i)^(<>|!=|>=?|<=?|==?)?\s*({}|dev)".format(_COMPLETE_VERSION)
)
