import importlib

import main
import util.labs
from objs.base_lab_config import BaseLabConfig
from util.labs import NON_PROD_LAB_CONFIGS, PROD_LAB_CONFIGS

import pytest
import pathlib
from bs4 import BeautifulSoup


class TestLabs:
    @pytest.mark.parametrize(
        "is_prod,labs",
        [
            ("false", NON_PROD_LAB_CONFIGS),
            ("true", PROD_LAB_CONFIGS),
        ],
    )
    def test_lab_conditional_set_is_prod(self, monkeypatch, is_prod, labs):
        monkeypatch.setenv("IS_PROD", is_prod)

        importlib.reload(util.labs)
        from util.labs import LAB_CONFIGS

        assert LAB_CONFIGS == labs

    def test_lab_conditional_not_set_is_prod(self, monkeypatch):
        monkeypatch.delenv("IS_PROD", raising=False)

        importlib.reload(util.labs)
        from util.labs import LAB_CONFIGS

        assert LAB_CONFIGS == NON_PROD_LAB_CONFIGS

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
        BaseLabConfig(**required_keys)
        # Make sure each lab has ALL the required keys:
        for lab_short_name, lab in util.labs.LAB_CONFIGS.items():
            lab_fields = set(lab.__dataclass_fields__.keys())
            required_fields = set(required_keys.keys())
            assert required_fields.issubset(lab_fields), (
                f"Lab '{lab_short_name}' is missing required keys"
            )

    def test_images_path_exist(self, monkeypatch):
        used_logos = set()
        for lab in (PROD_LAB_CONFIGS | NON_PROD_LAB_CONFIGS).values():
            if lab.logo:
                used_logos.add(lab.logo)

        LAMBDA_MAIN_PATH = pathlib.Path(__file__).resolve().parents[2]
        for logo in used_logos:
            assert pathlib.Path(LAMBDA_MAIN_PATH / "static" / "img" / logo).exists()

    def test_lab_not_healthy(self, lambda_context, fake_auth, helpers, monkeypatch):
        user = helpers.FakeUser()
        monkeypatch.setattr("portal.User", lambda *args, **kwargs: user)
        monkeypatch.setattr("util.auth.User", lambda *args, **kwargs: user)

        monkeypatch.setattr("objs.user.user.LAB_CONFIGS", helpers.FAKE_LAB_CONFIGS)

        monkeypatch.setattr("portal.Lab", lambda *args, **kwargs: helpers.FakeLab())

        event = helpers.get_event(path="/portal", cookies=fake_auth)
        ret = main.lambda_handler(event, lambda_context)

        soup = BeautifulSoup(ret["body"], "html.parser")
        test_lab_goto_button = soup.find("a", id="start-testlab")
        assert test_lab_goto_button["href"] == "#"
        assert test_lab_goto_button.get("disabled") is not None
        assert "unhealthy" in test_lab_goto_button["title"].lower()
