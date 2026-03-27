import sys
import os

# Add backend directory to path so relative imports inside backend work
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from main import app
