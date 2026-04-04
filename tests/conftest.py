"""Shared test configuration."""
import os

# Ensure TRELLO_API_KEY is set before any server imports
if not os.getenv("TRELLO_API_KEY"):
    os.environ["TRELLO_API_KEY"] = "test_api_key_placeholder"
