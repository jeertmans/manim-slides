"""
Lookup and merging of configuration files.

The configuration is gathered from multiple files, listed below by
increasing order of precedence:

1. the global configuration file (see :data:`GLOBAL_CONFIG_PATH`), e.g.,
   ``~/.config/manim-slides/manim-slides.toml`` on Linux;
2. local configuration files found in the current directory, or any of
   its parents, e.g., ``.manim-slides.toml``; when multiple files are
   found, the one closest to the current directory wins.

The same file structure as the local configuration file is used for the
global one, except that relative paths (e.g., ``folder``) are naturally
interpreted as relative to the current directory, not to the
configuration file.
"""

from collections.abc import Mapping
from pathlib import Path

import click
from pydantic import ValidationError

from .config import Config
from .defaults import CONFIG_PATH, GLOBAL_CONFIG_PATH
from .logger import logger

_MAX_PARENT_LEVELS = 100  # Guard against pathological (deep) folder trees


def list_local_config_files(
    folder: Path | None = None, config_path: Path | None = None
) -> list[Path]:
    """
    List local config files, ordered by increasing precedence.

    Start from FOLDER (defaults to the current directory) and walk up
    the folder tree, stopping at the root folder or at the first
    filesystem boundary (e.g., a mount point). All config files found
    along the way are returned, so the one closest to FOLDER comes last.
    """
    if config_path is None:
        config_name = CONFIG_PATH.name
    else:
        config_name = Path(config_path).name

    folder = Path(folder if folder is not None else Path.cwd()).resolve()

    # Walking up the folder tree yields files from the closest to the
    # furthest, so the list is reversed at the end to obtain an order of
    # increasing precedence (i.e., the closest file comes last).
    files: list[Path] = []

    for _ in range(_MAX_PARENT_LEVELS):
        config_file = folder / config_name

        if config_file.is_file():
            files.append(config_file)

        # Stop at the root folder or at a filesystem boundary (e.g., a
        # mount point), because config files above it will not be
        # relevant, see Flake8's behavior:
        # https://github.com/PyCQA/flake8/issues/498#issuecomment-812812244
        parent = folder.parent

        if parent == folder:
            break

        try:
            is_mount = parent.is_mount()
        except OSError:  # pragma: no cover
            is_mount = False

        if is_mount:
            break

        folder = parent

    return files[::-1]


def list_config_files(
    folder: Path | None = None, config_path: Path | None = None
) -> list[Path]:
    """
    List all config files that apply, ordered by increasing precedence.

    The global config file (see :data:`GLOBAL_CONFIG_PATH`) comes first,
    followed by local config files (see :func:`list_local_config_files`).
    An explicitly provided CONFIG_PATH is always included, even if it
    lives outside of the FOLDER tree (or outside of the current working
    directory).
    """
    files: list[Path] = []

    if GLOBAL_CONFIG_PATH.is_file():
        files.append(GLOBAL_CONFIG_PATH)

    files.extend(list_local_config_files(folder, config_path))

    if config_path is not None:
        config_path = Path(config_path).resolve()

        if config_path.is_file() and config_path not in files:
            files.append(config_path)

    return files


def load_merged_config(
    folder: Path | None = None, config_path: Path | None = None
) -> Config:
    """
    Load and merge all config files that apply, ordered by increasing
    precedence, and return the resulting configuration.

    Files that cannot be parsed are skipped, with a warning.
    """
    config = Config()

    for config_file in list_config_files(folder, config_path):
        logger.debug(f"Reading configuration file: {config_file}")

        try:
            new_config = Config.from_file(config_file)
        except (ValidationError, ValueError) as e:
            logger.warning(f"Ignoring invalid configuration file {config_file}: {e}")
            continue

        config = config.merge_with(new_config)

    return config


def validate_defaults_against_command(
    command: click.Command, defaults: Mapping[str, object]
) -> list[str]:
    """
    Check that option names in DEFAULTS are supported by COMMAND.

    Return the list of unknown option names.
    """
    param_names = {
        param.name for param in command.params if isinstance(param, click.Option)
    }

    return [key for key in defaults if key not in param_names]
