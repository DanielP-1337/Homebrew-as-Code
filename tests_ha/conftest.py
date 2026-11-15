"""Actual Home Assistant service/config-flow tests with synthetic sources."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield
