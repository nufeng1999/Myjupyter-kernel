import os
import sys
%cd "/root/Jupyter/Myjupyter-kernel/plugins"
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
