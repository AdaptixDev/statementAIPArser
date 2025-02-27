"""
Simple wrapper script to run the statement parser.
"""

import sys
from backend.src.main import main

if __name__ == "__main__":
    # Pass command line arguments to the main function
    sys.argv = sys.argv
    main() 