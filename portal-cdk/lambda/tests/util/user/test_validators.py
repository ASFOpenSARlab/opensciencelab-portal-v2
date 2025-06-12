import pytest


class TestValidators:
    def test_profile_validator_correct_filling(self):
        from util.user.validators import validate_profile

        fake_dict = {
            "country_of_residence": "",
            "is_affiliated_with_nasa": "",
            "user_or_pi_nasa_email": "",
            "user_affliated_with_nasa_research_email": "",
            "pi_affliated_with_nasa_research_email": "",
            "is_affiliated_with_us_gov_research": "",
            "user_affliated_with_gov_research_email": "",
            "is_affliated_with_isro_research": "",
            "user_affliated_with_isro_research_email": "",
            "is_affliated_with_university": "",
            "faculty_member_affliated_with_university": "",
            "research_member_affliated_with_university": "",
            "graduate_student_affliated_with_university": "",
        }

        ret = validate_profile(fake_dict)
        assert ret == fake_dict

    def test_profile_validator_wrong_filling(self):
        from util.user.validators import validate_profile

        fake_dict = {}

        with pytest.raises(ValueError):
            ret = validate_profile(fake_dict)
            assert ret == fake_dict
