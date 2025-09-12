"""
Swagger Helpers and Formatters

Use by importing the entire module, then call the specific endpoints
you need. (Or use format_response directly if it's custom for that area.)

from util import swagger
@access_router.get(
    "/users/<shortname>",
    # ...
    responses={
        **swagger.format_response(
            example={
                "users": [
                    {"username": "user1", "labs": {}, "access": []},
                ],
                "message": "OK",
            },
            description="Returns users that can access the lab.",
            code=200,
        ),
        **swagger.code_403,
        **swagger.code_404_lab_not_found,
    },
    tags=[access_route["name"]],
)
"""


# Swagger Dict example: https://swagger.io/docs/specification/v3_0/data-models/dictionaries/#fixed-keys
# Swagger objects: https://swagger.io/docs/specification/v3_0/data-models/data-types/#objects
def format_response(
    example: dict,
    description: str = "",
    code: int = 200,
) -> dict:
    response = {
        "content": {
            "application/json": {
                "example": example,
            },
        },
    }
    if description:
        response["description"] = description
    return {code: response}


code_200_result_success = format_response(
    example={"result": "Success"},
    description="Returns a dict saying it was successful.",
    code=200,
)

code_400_json = format_response(
    example={"result": "Does not contain 'labs' key"},
    description="Bad Request - the data provided was not json.",
    code=400,
)

code_403 = format_response(
    example={"error": "User not logged in"},
    description="Forbidden - the caller doesn't have admin access.",
    code=403,
)

code_404_lab_not_found = format_response(
    example={"error": "Lab not found"},
    description="Lab not found.",
    code=404,
)

code_404_user_not_found = format_response(
    example={"error": "User not found"},
    description="User not found.",
    code=404,
)

code_422 = format_response(
    example={"result": "Does not contain 'labs' key"},
    description="Unprocessable Entity - the dict provided didn't pass validation.",
    code=422,
)
