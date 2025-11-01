import logging
from pathlib import Path

def get_logger(name: str, log_to_file: bool = False, log_dir: str = "logs") -> logging.Logger:
    """
    Creates and returns a logger with console and optional file output.

    Arguments:
        name (str): Name of the logger (usually __name__).
        log_to_file (bool): Whether to also log to a file.
        log_dir (str): Directory to store log files if file logging is enabled.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Prevent duplicate logs in parent loggers

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Optional file handler
        if log_to_file:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(f"{log_dir}/{name}.log", encoding="utf-8")
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    return logger