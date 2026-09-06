import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skip(reason="Requires Junior 1 language plugins and Junior 2 sandbox/scanner")
def test_live_python_and_c_execution():
    assert False
