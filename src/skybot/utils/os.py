import os
from shutil import copy
from pkgutil import get_loader

def get_package_directory(package_name: str) -> str:
    """Get the directory of a package."""
    loader = get_loader(package_name)
    if loader is None or loader.is_package(package_name):
        return os.path.dirname(loader.get_filename())
    else:
        raise ValueError(f"Package '{package_name}' not found")

def copy_assets(source_dir: str, destination_dir: str) -> None:
    """Copy boilerplate assets from source to destination."""
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    for root, dirs, files in os.walk(source_dir):
        for dir_name in dirs:
            dest_path = os.path.join(destination_dir, dir_name)
            os.makedirs(dest_path, exist_ok=True)
        for file_name in files:
            src_file = os.path.join(root, file_name)
            dest_file = os.path.join(destination_dir, file_name)
            copy(src_file, dest_file)
