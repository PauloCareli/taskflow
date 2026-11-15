import os

# `taskapp.main` builds the app from settings at import time, so a signing secret must exist
# before any test module imports it. Tests that exercise the secret rules set their own.
os.environ.setdefault("TASKAPP_JWT_SECRET", "test-suite-secret-that-is-long-enough-for-hs256")
