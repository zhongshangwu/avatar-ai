import argparse
import sys
import yaml
import logging
from typing import List, Dict, Union


logger = logging.getLogger(__name__)


class StoreBoolean(argparse.Action):
    """Action to store a boolean value."""

    def __init__(self, option_strings, dest, default=None, required=False, help=None):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            const=None,
            default=default,
            required=required,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)

class SortedHelpFormatter(argparse.HelpFormatter):
    """Help formatter that sorts the arguments alphabetically."""

    def add_arguments(self, actions):
        actions = sorted(actions, key=lambda action: action.dest)
        super().add_arguments(actions)


class FlexibleArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that allows both underscore and dash in names."""

    def __init__(self, *args, **kwargs):
        # 设置默认的 'formatter_class' 为 SortedHelpFormatter
        if 'formatter_class' not in kwargs:
            kwargs['formatter_class'] = SortedHelpFormatter
        super().__init__(*args, **kwargs)

    def parse_args(self, args=None, namespace=None):
        if args is None:
            args = sys.argv[1:]

        if '--config' in args:
            args = self._pull_args_from_config(args)

        # 在参数名称中转换下划线为破折号，反之亦然
        processed_args = []
        for arg in args:
            if arg.startswith('--'):
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    key = '--' + key[len('--'):].replace('_', '-')
                    processed_args.append(f'{key}={value}')
                else:
                    processed_args.append('--' +
                                          arg[len('--'):].replace('_', '-'))
            elif arg.startswith('-O') and arg != '-O' and len(arg) > 2:
                # 允许不带空格使用 -O 标志，例如 -O3
                processed_args.append('-O')
                processed_args.append(arg[2:])
            else:
                processed_args.append(arg)

        return super().parse_args(processed_args, namespace)

    def _pull_args_from_config(self, args: List[str]) -> List[str]:
        """从配置文件中提取参数并添加到命令行参数变量中。

        配置文件中的参数将被插入到参数列表中。

        例如:
        ```yaml
            port: 12323
            tensor-parallel-size: 4
        ```
        ```python
        $: vllm {serve,chat,complete} "facebook/opt-12B" \
            --config config.yaml -tp 2
        $: args = [
            "serve,chat,complete",
            "facebook/opt-12B",
            '--config', 'config.yaml',
            '-tp', '2'
        ]
        $: args = [
            "serve,chat,complete",
            "facebook/opt-12B",
            '--port', '12323',
            '--tensor-parallel-size', '4',
            '-tp', '2'
            ]
        ```

        请注意配置参数是如何在子命令之后插入的。
        这样在super()解析这些参数时，优先级顺序得以维持。
        """
        assert args.count(
            '--config') <= 1, "指定了多个配置文件！"

        index = args.index('--config')
        if index == len(args) - 1:
            raise ValueError("未指定配置文件！请检查您的命令行参数。")

        file_path = args[index + 1]

        config_args = self._load_config_file(file_path)

        # 第0个索引用于 {serve,chat,complete}
        # 然后是 model_tag（仅用于serve）
        # 然后是配置参数
        # 然后是其余的命令行参数。
        # 保持这个顺序将强制执行优先级：cli > config > defaults
        if args[0] == "serve":
            if index == 1:
                raise ValueError(
                    "未指定model_tag！请检查您的命令行参数。")
            args = [args[0]] + [
                args[1]
            ] + config_args + args[2:index] + args[index + 2:]
        else:
            args = [args[0]] + config_args + args[1:index] + args[index + 2:]

        return args

    def _load_config_file(self, file_path: str) -> List[str]:
        """加载yaml文件并将键值对作为扁平化列表返回，格式类似于argparse
        ```yaml
            port: 12323
            tensor-parallel-size: 4
        ```
        返回:
            processed_args: list[str] = [
                '--port': '12323',
                '--tensor-parallel-size': '4'
            ]
        """

        extension: str = file_path.split('.')[-1]
        if extension not in ('yaml', 'yml'):
            raise ValueError(
                f"配置文件必须是yaml/yml类型。提供了{extension}")

        # 只期望原子类型的扁平字典
        processed_args: List[str] = []

        config: Dict[str, Union[int, str]] = {}
        try:
            with open(file_path) as config_file:
                config = yaml.safe_load(config_file)
        except Exception as ex:
            logger.error(
                "无法读取位于%s的配置文件。确保路径正确", file_path)
            raise ex

        store_boolean_arguments = [
            action.dest for action in self._actions
            if isinstance(action, StoreBoolean)
        ]

        for key, value in config.items():
            if isinstance(value, bool) and key not in store_boolean_arguments:
                if value:
                    processed_args.append('--' + key)
            else:
                processed_args.append('--' + key)
                processed_args.append(str(value))

        return processed_args