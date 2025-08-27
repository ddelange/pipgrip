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

"""
Tests for --skip-invalid-input functionality and exception handling.

Exception Type Behavior Across Python Versions:

In Python 2.7:
- pkg_resources.Requirement.parse() raises RequirementParseError for invalid syntax
- RequirementParseError inherits from ValueError (not InvalidRequirement)
- RequirementParseError and InvalidRequirement are separate, unrelated exception types
- Test patterns like 'invalid::syntax' trigger RequirementParseError

In Python 3.x:
- pkg_resources.Requirement.parse() raises InvalidRequirement for invalid syntax
- RequirementParseError exists but inherits from InvalidRequirement for backward compatibility
- RequirementParseError is never actually raised in practice
- Same test patterns like 'invalid::syntax' trigger InvalidRequirement

CLI Exception Handler Coverage:
The CLI catches both exception types: `except (InvalidRequirement, RequirementParseError)`
- Python 2.7: Catches RequirementParseError (primary) and InvalidRequirement (fallback)
- Python 3.x: Catches InvalidRequirement (primary) with RequirementParseError inheritance

Test Coverage:
- All test patterns in this file test the InvalidRequirement path in Python 3.x
- The same test patterns test the RequirementParseError path in Python 2.7
- The exception handler correctly processes both types across Python versions
"""

import os
import tempfile

from click.testing import CliRunner

from pipgrip.cli import main


def test_skip_invalid_input_argument_parsing():
    """Test that --skip-invalid-input flag is correctly parsed."""
    runner = CliRunner()

    # Test help includes the new option
    result = runner.invoke(main, ["--help"])
    assert "--skip-invalid-input" in result.output
    assert "Skip invalid requirements" in result.output


def test_skip_invalid_input_with_direct_arguments(caplog):
    """Test --skip-invalid-input flag with direct command line arguments."""
    runner = CliRunner()

    # Test with invalid requirement as direct argument
    result = runner.invoke(main, ["invalid::syntax", "--skip-invalid-input", "-v"])

    # Should succeed and log warning
    assert result.exit_code == 0
    assert "Skipping invalid requirement 'invalid::syntax'" in caplog.text


def test_skip_invalid_input_without_flag_fails():
    """Test that invalid requirements fail without --skip-invalid-input flag."""
    runner = CliRunner()

    # Test with invalid requirement as direct argument (should fail)
    result = runner.invoke(main, ["invalid::syntax"])

    # Should fail
    assert result.exit_code != 0
    assert "::syntax" in str(result.exception)


def test_skip_invalid_input_with_requirements_file():
    """Test --skip-invalid-input flag with requirements file."""
    runner = CliRunner()

    # Create temporary requirements file with mixed valid/invalid entries
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("requests==2.22.0\n")
        f.write("invalid::syntax\n")
        f.write("# comment line\n")
        f.write("six\n")
        f.write("another::invalid::entry\n")
        temp_file = f.name

    try:
        # Test without flag - should fail on first invalid requirement
        result = runner.invoke(main, ["-r", temp_file])
        assert result.exit_code != 0
        assert "::syntax" in str(result.exception)

        # Test with flag - should skip invalid requirements and succeed
        result = runner.invoke(main, ["-r", temp_file, "--skip-invalid-input", "-v"])
        assert result.exit_code == 0
        # Should process valid requirements
        assert "requests" in result.output or "six" in result.output

    finally:
        os.unlink(temp_file)


def test_skip_invalid_input_mixed_sources(caplog):
    """Test --skip-invalid-input with mixed direct args and requirements file."""
    runner = CliRunner()

    # Create temporary requirements file with invalid entry
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("six>=1.0\n")  # Use a real package that exists
        f.write("invalid::file::syntax\n")
        temp_file = f.name

    try:
        # Test mixed valid direct arg, invalid direct arg, and requirements file
        result = runner.invoke(
            main,
            [
                "requests==2.22.0",  # valid direct arg
                "invalid::direct::syntax",  # invalid direct arg
                "-r",
                temp_file,  # requirements file with mixed entries
                "--skip-invalid-input",
                "-v",
            ],
        )

        assert result.exit_code == 0
        # Should log warnings for both invalid entries
        assert "Skipping invalid requirement 'invalid::direct::syntax'" in caplog.text
        assert "Skipping invalid requirement 'invalid::file::syntax'" in caplog.text
        # Should process the valid requirements
        assert "requests" in result.output or "six" in result.output

    finally:
        os.unlink(temp_file)


def test_skip_invalid_input_flag_with_empty_args():
    """Test --skip-invalid-input flag with no other args produces empty output."""
    runner = CliRunner()

    result = runner.invoke(main, ["--skip-invalid-input"])

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
    assert "pipgrip, version {}".format(__version__) in result.output
