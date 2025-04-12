"""
-*- coding: utf-8 -*-
PrintNestDict.py -
Author：Administrator
Date:2025-04-05
"""


def print_nested_dict(d, indent=0):
    """
    递归打印嵌套字典的所有内容

    :param d: 要打印的字典（或嵌套字典）
    :param indent: 当前缩进级别（默认0，用于格式化输出）
    """
    for key, value in d.items():
        # 处理嵌套字典的情况
        if isinstance(value, dict):
            print('  ' * indent + f"{key}:")
            print_nested_dict(value, indent + 1)  # 递归调用，增加缩进
        else:
            print('  ' * indent + f"{key}: {value}")  # 非字典值直接打印