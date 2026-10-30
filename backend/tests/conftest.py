import os
import tempfile

# Point the app at a throwaway data folder before it is imported.
os.environ["EBYAFAAYO_DATA"] = tempfile.mkdtemp(prefix="ebyafaayo-test-")
os.environ.setdefault("EBYAFAAYO_TEMPORAL", "off")  # test_durable.py starts its own Temporal server
