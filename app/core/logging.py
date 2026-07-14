import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a consistent format for CLI and dashboard."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
