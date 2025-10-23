import importlib

import util.labs
from util.labs import BaseLab, NON_PROD_LABS, PROD_LABS

import pytest
import pathlib


class TestLabs:
    @pytest.mark.parametrize(
        "is_prod,labs",
        [
            ("false", NON_PROD_LABS),
            ("true", PROD_LABS),
        ],
    )
    def test_lab_conditional_set_is_prod(self, monkeypatch, is_prod, labs):
        monkeypatch.setenv("IS_PROD", is_prod)

        importlib.reload(util.labs)
        from util.labs import LABS

        assert LABS == labs

    def test_lab_conditional_not_set_is_prod(self, monkeypatch):
        monkeypatch.delenv("IS_PROD", raising=False)

        importlib.reload(util.labs)
        from util.labs import LABS

        assert LABS == NON_PROD_LABS

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

    def test_images_path_exist(self, monkeypatch):
        used_logos = set()
        for lab in (PROD_LABS | NON_PROD_LABS).values():
            if lab.logo:
                used_logos.add(lab.logo)

        for logo in used_logos:
            assert pathlib.Path(f"./portal-cdk/lambda_main/static/img/{logo}").exists()
