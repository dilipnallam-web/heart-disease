"""
Vercel Serverless Function Entrypoint for CardioPredict Flask API.
Routes all /api/* requests to Flask application.
"""
import os
import sys

# Ensure repository root is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app import app

# Vercel looks for 'app' as the WSGI application instance
application = app
