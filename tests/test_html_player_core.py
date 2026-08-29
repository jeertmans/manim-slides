import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
def test_player_core_state_machine(project_folder: Path) -> None:
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(  # nosec B603
        [node, "--test", "tests/player_core.test.cjs"],
        cwd=project_folder,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
