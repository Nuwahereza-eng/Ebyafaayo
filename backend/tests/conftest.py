import os
import tempfile

# Point the app at a throwaway data folder before it is imported.
os.environ["EBYAFAAYO_DATA"] = tempfile.mkdtemp(prefix="ebyafaayo-test-")
