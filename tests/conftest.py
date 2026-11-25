import sys
from pathlib import Path

# Make project-root imports (config, rag, graph, backend) work in tests.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import tempfile

# Tests use a throwaway database and vector store, never your real ones.
_tmp = tempfile.mkdtemp()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ.setdefault("CHROMA_DB_DIR", f"{_tmp}/chroma")
