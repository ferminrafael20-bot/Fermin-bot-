import pytest


@pytest.fixture(autouse=True)
def moneda_usd(monkeypatch, request):
    """Las pruebas antiguas usan dólares; las de pesos chilenos lo cambian."""
    if "clp" not in request.node.name:
        monkeypatch.setenv("ALFRED_MONEDA", "USD")
