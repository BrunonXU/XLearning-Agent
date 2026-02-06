import streamlit as st
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(__file__))

# Delegate directly to the new UI app
from src.ui.app import main

if __name__ == "__main__":
    main()
