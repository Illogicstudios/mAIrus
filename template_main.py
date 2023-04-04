import sys
import os
import importlib

if __name__ == '__main__':
    # TODO specify the right path
    install_dir = 'PATH/TO/mAIrus'
    if not sys.path.__contains__(install_dir):
        sys.path.append(install_dir)

    # TODO Change if needed
    __PATH_TO_OPENAI_KEY = 'PATH/TO/openai_key'

    modules = [
        "MAIrus"
        "Model",
    ]

    from utils import *
    unload_packages(silent=True, packages=modules)

    for module in modules:
        importlib.import_module(module)

    from MAIrus import *

    try:
        mAIrus.close()
    except:
        pass
    mAIrus = MAIrus(__PATH_TO_OPENAI_KEY)
    mAIrus.show()