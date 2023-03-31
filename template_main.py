import sys
import importlib

if __name__ == '__main__':
    # TODO specify the right path
    install_dir = 'PATH/TO/mAIrus'
    if not sys.path.__contains__(install_dir):
        sys.path.append(install_dir)

    modules = [
        "MAIrus"
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
    mAIrus = MAIrus()
    mAIrus.show()