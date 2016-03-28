#!/usr/bin/python
import sys
import os

sys.path.insert(0,'/opt/adreset2/git')
os.chdir('/opt/adreset2/git')

activate_this = '/opt/adreset2/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from adreset2 import app as application
