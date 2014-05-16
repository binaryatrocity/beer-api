import sys
import os

directory = os.path.dirname(os.path.realpath(__file__))
activator = os.path.join(directory, 'venv/bin/activate_this.py')
execfile(activator, dict(__file__=activator))
sys.path.append(directory)

from app import app as application
