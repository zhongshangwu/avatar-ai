import datetime
import json
import logging
import os
import sys
from functools import lru_cache, partial
from logging import Logger
from logging.config import dictConfig
from os import path
from types import MethodType
from typing import Any, Optional, cast

# 环境变量定义
AVATARAI_CONFIGURE_LOGGING = os.environ.get("AVATARAI_CONFIGURE_LOGGING", "1") == "1"
AVATARAI_LOGGING_CONFIG_PATH = os.environ.get("AVATARAI_LOGGING_CONFIG_PATH", "")
AVATARAI_LOGGING_LEVEL = os.environ.get("AVATARAI_LOGGING_LEVEL", "INFO")
AVATARAI_LOGGING_PREFIX = os.environ.get("AVATARAI_LOGGING_PREFIX", "[AvatarAI] ")

_FORMAT = (f"{AVATARAI_LOGGING_PREFIX}%(levelname)s %(asctime)s "
           "%(filename)s:%(lineno)d] %(message)s")
_DATE_FORMAT = "%m-%d %H:%M:%S"

DEFAULT_LOGGING_CONFIG = {
    "formatters": {
        "avatarai": {
            "class": "avatarai.utils.logging_utils.NewLineFormatter",
            "datefmt": _DATE_FORMAT,
            "format": _FORMAT,
        },
    },
    "handlers": {
        "avatarai": {
            "class": "logging.StreamHandler",
            "formatter": "avatarai",
            "level": AVATARAI_LOGGING_LEVEL,
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "avatarai": {
            "handlers": ["avatarai"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "version": 1,
    "disable_existing_loggers": False
}


@lru_cache
def _print_info_once(logger: Logger, msg: str) -> None:
    # 设置 stacklevel 为 2 以显示原始调用者的行信息
    logger.info(msg, stacklevel=2)


@lru_cache
def _print_warning_once(logger: Logger, msg: str) -> None:
    # 设置 stacklevel 为 2 以显示原始调用者的行信息
    logger.warning(msg, stacklevel=2)


class _AvatarAILogger(Logger):
    """
    注意:
        此类仅提供类型信息。
        我们直接在 :class:`logging.Logger` 实例上修补方法，
        以避免与其他库冲突。
    """

    def info_once(self, msg: str) -> None:
        """
        与 :meth:`info` 相同，但使用相同消息的后续调用会被静默丢弃。
        """
        _print_info_once(self, msg)

    def warning_once(self, msg: str) -> None:
        """
        与 :meth:`warning` 相同，但使用相同消息的后续调用会被静默丢弃。
        """
        _print_warning_once(self, msg)


def _configure_avatarai_root_logger() -> None:
    logging_config = dict[str, Any]()

    if not AVATARAI_CONFIGURE_LOGGING and AVATARAI_LOGGING_CONFIG_PATH:
        raise RuntimeError(
            "AVATARAI_CONFIGURE_LOGGING 被评估为 false，但提供了 "
            "AVATARAI_LOGGING_CONFIG_PATH。AVATARAI_LOGGING_CONFIG_PATH "
            "隐含 AVATARAI_CONFIGURE_LOGGING。请启用 "
            "AVATARAI_CONFIGURE_LOGGING 或取消设置 AVATARAI_LOGGING_CONFIG_PATH。")

    if AVATARAI_CONFIGURE_LOGGING:
        logging_config = DEFAULT_LOGGING_CONFIG

    if AVATARAI_LOGGING_CONFIG_PATH:
        if not path.exists(AVATARAI_LOGGING_CONFIG_PATH):
            raise RuntimeError(
                "无法加载日志配置。文件不存在: %s",
                AVATARAI_LOGGING_CONFIG_PATH)
        with open(AVATARAI_LOGGING_CONFIG_PATH, encoding="utf-8") as file:
            custom_config = json.loads(file.read())

        if not isinstance(custom_config, dict):
            raise ValueError("无效的日志配置。期望字典，得到 %s。",
                             type(custom_config).__name__)
        logging_config = custom_config

    if logging_config:
        dictConfig(logging_config)


def init_logger(name: str) -> _AvatarAILogger:
    """此函数的主要目的是确保以这样的方式检索记录器，
    可以确保根 avatarai 记录器已经配置好。"""

    logger = logging.getLogger(name)

    methods_to_patch = {
        "info_once": _print_info_once,
        "warning_once": _print_warning_once,
    }

    for method_name, method in methods_to_patch.items():
        setattr(logger, method_name, MethodType(method, logger))

    return cast(_AvatarAILogger, logger)


# 当模块被导入时，根记录器被初始化。
# 这是线程安全的，因为模块只被导入一次，
# 由 Python GIL 保证。
_configure_avatarai_root_logger()

logger = init_logger(__name__)


def _trace_calls(log_path, root_dir, frame, event, arg=None):
    if event in ['call', 'return']:
        # 提取文件名、行号、函数名和代码对象
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        func_name = frame.f_code.co_name
        if not filename.startswith(root_dir):
            # 只记录 avatarai root_dir 中的函数
            return
        # 记录每个函数调用或返回
        try:
            last_frame = frame.f_back
            if last_frame is not None:
                last_filename = last_frame.f_code.co_filename
                last_lineno = last_frame.f_lineno
                last_func_name = last_frame.f_code.co_name
            else:
                # 初始帧
                last_filename = ""
                last_lineno = 0
                last_func_name = ""
            with open(log_path, 'a') as f:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                if event == 'call':
                    f.write(f"{ts} 调用"
                            f" {func_name} 在 {filename}:{lineno}"
                            f" 来自 {last_func_name} 在 {last_filename}:"
                            f"{last_lineno}\n")
                else:
                    f.write(f"{ts} 返回自"
                            f" {func_name} 在 {filename}:{lineno}"
                            f" 到 {last_func_name} 在 {last_filename}:"
                            f"{last_lineno}\n")
        except NameError:
            # 关闭期间模块被删除
            pass
    return partial(_trace_calls, log_path, root_dir)


def enable_trace_function_call(log_file_path: str,
                               root_dir: Optional[str] = None):
    """
    启用跟踪 `root_dir` 下的代码中的每个函数调用。
    这对调试挂起或崩溃很有用。
    `log_file_path` 是日志文件的路径。
    `root_dir` 是要跟踪的代码的根目录。如果为 None，则为 avatarai 根目录。

    请注意，此调用是线程级的，任何调用此函数的线程都将启用跟踪。
    其他线程不受影响。
    """
    logger.warning(
        "AVATARAI_TRACE_FUNCTION 已启用。它将记录 Python 执行的每个"
        " 函数。这将使代码运行变慢。建议"
        "仅用于调试挂起或崩溃。")
    logger.info("跟踪帧日志保存到 %s", log_file_path)
    if root_dir is None:
        # 默认情况下，这是 avatarai 根目录
        root_dir = os.path.dirname(os.path.dirname(__file__))
    sys.settrace(partial(_trace_calls, log_file_path, root_dir))
