import os
import sys
import time
import logging
import yaml

output_dir_name_prefix = os.path.join(f"{os.path.splitext(os.path.basename(sys.argv[0]))[0]}",
                                      f"{time.strftime('%Y%m%d%H%M%S')}_{os.getpid()}")
output_dir_path = None
output_dir_generated = False


def yaml_load_file(path):
    with open(path, encoding="utf-8") as f:
        obj = yaml.load(f)
    return obj


def yaml_dump_file(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(obj, f, default_flow_style=False)


def get_output_dir():
    """
    デフォルトの計算結果ファイル出力ディレクトリを取得する。
    :return: ディレクトリのパス。
    """
    global output_dir_generated, output_dir_path
    if not output_dir_generated:
        output_dir_path = os.path.join("run", output_dir_name_prefix)
        os.makedirs(output_dir_path)
        output_dir_generated = True
        sys.stderr.write(f"Output directory: {output_dir_path}\n")
    return output_dir_path


def get_output_filename(basename):
    return os.path.join(get_output_dir(), basename)


def get_logger(name):
    if name == "__main__":
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(os.path.join(get_output_dir(), "log.log"))
        file_handler.setLevel(logging.INFO)
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stderr_handler)
        root_logger.info(f"args: {sys.argv}")
    return logging.getLogger(name)
