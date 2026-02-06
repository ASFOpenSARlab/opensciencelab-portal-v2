"""A list of validators, for custom parsing input data."""

VALID_ACCESS_REQUEST_STATES = [
    "new",
    "approved",
    "rejected",
    "pending",
]

REQUIRED_ANSWER_FIELDS = [
    "sar_experience",
    "osl_experience",
    "use_case",
    "personal_impacts",
    "community_impacts",
    "research_impacts",
    "submission_date",
    "submission_ip",
    "submission_cc",
]


def validate_access_requests(requests: list) -> list:
    """

    Args:
        requests:

            [
              {
                "username": "osl-username",
                "answers":[   # List of Dicts so we can allow updating and keep a record.
                  {
                    "sar_experience": "...",
                    "osl_experience": "...",
                    "use_case": "...",
                    "personal_impacts": "...",
                    "community_impacts": "...",
                    "research_impacts": "...",
                    "submission_date": "...",
                    "submission_ip": "...",
                    "submission_cc": "...",
                  }
                ],
                "status": "new|approved|rejected|pending",
              }
            ]

    Returns:
        validated requests structure


    """
    # make sure it's a dict

    if not isinstance(requests, list):
        raise ValueError("access_requests must be a list of dicts")

    for request in requests:
        if not isinstance(request, dict):
            raise ValueError("access_requests must be a list of dicts")

        for field in ("username", "status", "answers"):
            if field not in request:
                raise ValueError(f"access_requests dicts must contain '{field}'")

        if request["status"] not in VALID_ACCESS_REQUEST_STATES:
            raise ValueError(
                f"access_requests status {request['status']} not in {VALID_ACCESS_REQUEST_STATES}"
            )

        if not isinstance(request["answers"], list):
            raise ValueError("access_requests request answers must be a list of dicts")

        for answer_set in request["answers"]:
            if not isinstance(answer_set, dict):
                raise ValueError("access_requests request answers must a list of dicts")
            for field in REQUIRED_ANSWER_FIELDS:
                if field not in answer_set:
                    raise ValueError(
                        f"access_requests request answer set ({answer_set}) must contain {field}"
                    )

    # If we get here, the request is valid:
    return requests
