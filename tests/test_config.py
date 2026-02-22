import os
import pytest
import sys
from unittest.mock import patch

# Add the root directory to sys.path so we can import src
sys.path.append(os.getcwd())

def test_store_raises_error_when_database_url_missing():
    # Ensure src.store is not in sys.modules so it runs the top-level code
    if 'src.store' in sys.modules:
        del sys.modules['src.store']

    # We also need to remove DATABASE_URL if it happens to be set in the environment
    # Using patch.dict to clear environment for this test block
    with patch.dict(os.environ, clear=True):
        # Explicitly remove it just in case patch didn't catch it (though it should)
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

        with pytest.raises(ValueError, match="DATABASE_URL environment variable is not set"):
            import src.store

def test_store_loads_when_database_url_set():
    if 'src.store' in sys.modules:
        del sys.modules['src.store']

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/testdb"}):
        import src.store
        assert src.store.DATABASE_URL == "postgresql://test:test@localhost:5432/testdb"
