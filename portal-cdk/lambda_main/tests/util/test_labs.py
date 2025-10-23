import importlib

import util.labs
from util.labs import BaseLab


class TestLabs:
    def test_lab_conditional_non_prod(self, monkeypatch):
        monkeypatch.setenv("IS_PROD", "false")

        importlib.reload(util.labs)

        assert "smce-test-opensarlab" in util.labs.LABS.keys()
        assert "smce-prod-opensarlab" not in util.labs.LABS.keys()

    def test_lab_conditional_prod(self, monkeypatch):
        monkeypatch.setenv("IS_PROD", "true")

        importlib.reload(util.labs)

        assert "smce-test-opensarlab" not in util.labs.LABS.keys()
        assert "smce-prod-opensarlab" in util.labs.LABS.keys()

    def test_lab_required_keys(self):
        required_keys = {
            "friendly_name": "test-name",
            "short_lab_name": "test-short-name",
            "accessibility": "private",
            "allowed_profiles": ["m6a.large"],
            "deployment_url": "https://example.com",
        }
        # Make sure the keys are, in fact, required:
        # (this will throw if any are missing.
        #  Force us to keep the above list updated)
        BaseLab(**required_keys)
        # Make sure each lab has ALL the required keys:
        for lab_short_name, lab in util.labs.LABS.items():
            lab_fields = set(lab.__dataclass_fields__.keys())
            required_fields = set(required_keys.keys())
            assert required_fields.issubset(lab_fields), (
                f"Lab '{lab_short_name}' is missing required keys"
            )
