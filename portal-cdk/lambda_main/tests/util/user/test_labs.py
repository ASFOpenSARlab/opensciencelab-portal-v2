import importlib


class TestLabs:
    def test_lab_conditional_non_prod(self, monkeypatch):
        monkeypatch.setenv("IS_PROD", "false")
        import util.labs

        importlib.reload(util.labs)

        assert "smce-test-opensarlab" in util.labs.LABS.keys()
        assert "smce-prod-opensarlab" not in util.labs.LABS.keys()

    def test_lab_conditional_prod(self, monkeypatch):
        monkeypatch.setenv("IS_PROD", "true")
        import util.labs

        importlib.reload(util.labs)

        assert "smce-test-opensarlab" not in util.labs.LABS.keys()
        assert "smce-prod-opensarlab" in util.labs.LABS.keys()
