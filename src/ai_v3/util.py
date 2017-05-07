import sys
import os
import time
import logging

OUTPUT_BASEDIR = "../../log"
OUTPUT_DIR: str = None


def _logger_filter(record: logging.LogRecord):
    if record.name.startswith("chainerrl"):
        # chainerrlから大量のログが吐かれるので抑制
        return 0
    return 1


def _init_logger():
    file_handler = logging.FileHandler(os.path.join(OUTPUT_DIR, "run.log"), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(stderr_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    file_handler.addFilter(_logger_filter)
    stderr_handler.addFilter(_logger_filter)


def init(suffix=None):
    global OUTPUT_DIR
    if OUTPUT_DIR:
        return

    OUTPUT_DIR = os.path.join(OUTPUT_BASEDIR, time.strftime("%y%m%d%H%M%S") + "_" + suffix)
    os.mkdir(OUTPUT_DIR)

    _init_logger()


def get_output_dir():
    global OUTPUT_DIR
    return OUTPUT_DIR
