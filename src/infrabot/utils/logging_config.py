import logging
import sys


def setup_logging(debug_mode=False):
    """Configure logging for the infrabot package."""
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger("infrabot")
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Prevent log messages from being propagated to the root logger
    root_logger.propagate = False

    return root_logger
