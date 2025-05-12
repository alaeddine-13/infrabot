import os
from shutil import copy
from pkgutil import get_loader
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_package_directory(package_name: str) -> str:
    """Get the directory of a package."""
    loader = get_loader(package_name)
    if loader is None or loader.is_package(package_name):
        return os.path.dirname(loader.get_filename())
    else:
        raise ValueError(f"Package '{package_name}' not found")


def copy_assets(
    source_dir: str, destination_dir: str, whitelist: Optional[list[str]] = None
) -> None:
    """Copy boilerplate assets from source to destination."""
    if not whitelist:
        whitelist = []

    try:
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        for root, dirs, files in os.walk(source_dir):
            for file_name in files:
                if whitelist and file_name not in whitelist:
                    continue
                src_file = os.path.join(root, file_name)
                dest_file = os.path.join(destination_dir, file_name)
                try:
                    copy(src_file, dest_file)
                except (OSError, IOError) as e:
                    logger.error(
                        f"Failed to copy file {src_file} to {dest_file}: {str(e)}"
                    )
                    raise
    except Exception as e:
        logger.error(f"Error during asset copy operation: {str(e)}")
        raise
