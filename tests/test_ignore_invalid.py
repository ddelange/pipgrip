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
import logging
import tempfile
import os

import pytest
from click.testing import CliRunner

from pipgrip.cli import main
from pipgrip.pipper import read_requirements


def test_ignore_invalid_argument_parsing():
    """Test that --ignore-invalid flag is correctly parsed."""
    runner = CliRunner()
    
    # Test help includes the new option
    result = runner.invoke(main, ["--help"])
    assert "--ignore-invalid" in result.output
    assert "Ignore invalid requirements" in result.output


def test_read_requirements_ignore_invalid(caplog):
    """Test read_requirements function with ignore_invalid parameter.""" 
    caplog.set_level(logging.WARNING)
    
    # Create temporary requirements file with mixed valid/invalid entries
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("requests==2.22.0\n")
        f.write("invalid::syntax\n")
        f.write("# comment line\n")
        f.write("six\n")
        f.write("http://invalid-url::format\n")
        temp_file = f.name
    
    try:
        # Test with ignore_invalid=False (should include invalid requirements)
        reqs_no_ignore = read_requirements(temp_file, ignore_invalid=False)
        assert "requests==2.22.0" in reqs_no_ignore
        assert "invalid::syntax" in reqs_no_ignore
        assert "six" in reqs_no_ignore
        assert "http://invalid-url::format" in reqs_no_ignore
        # Comments should be filtered out
        assert len([r for r in reqs_no_ignore if r.startswith("#")]) == 0
        
        # Clear the log
        caplog.clear()
        
        # Test with ignore_invalid=True (should filter out invalid requirements)
        reqs_ignore = read_requirements(temp_file, ignore_invalid=True)
        assert "requests==2.22.0" in reqs_ignore
        assert "six" in reqs_ignore
        assert "invalid::syntax" not in reqs_ignore
        assert "http://invalid-url::format" not in reqs_ignore
        
        # Check that warnings were logged
        assert "Ignoring invalid requirement 'invalid::syntax'" in caplog.text
        assert "Ignoring invalid requirement 'http://invalid-url::format'" in caplog.text
        
    finally:
        os.unlink(temp_file)


def test_ignore_invalid_without_flag_fails():
    """Test that invalid requirements fail without --ignore-invalid flag."""
    runner = CliRunner()
    
    # Create temporary requirements file with invalid entry
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("invalid::syntax\n")
        temp_file = f.name
    
    try:
        result = runner.invoke(main, ["-r", temp_file])
        
        # Should fail
        assert result.exit_code != 0
        assert "invalid::syntax" in str(result.exception)
        
    finally:
        os.unlink(temp_file)


def test_ignore_invalid_flag_with_empty_args():
    """Test --ignore-invalid flag with no other args produces empty output.""" 
    runner = CliRunner()
    
    result = runner.invoke(main, ["--ignore-invalid"])
    
    # Should succeed with empty output
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_version_flag():
    """Test --version flag displays the correct version."""
    from pipgrip import __version__
    runner = CliRunner()
    
    result = runner.invoke(main, ["--version"])
    
    # Should succeed and display version
    assert result.exit_code == 0
    assert f"pipgrip, version {__version__}" in result.output
