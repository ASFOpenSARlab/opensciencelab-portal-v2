# Lambda Main

The Core of the project. This function holds all the API/UI logic for the portal itself.

## Directory Structure

- [`data/`](./data/): Contains static data files used by the Lambda function.
- [`objs/`](./objs/): Contains objects used to communicate with dynamoDB.
- [`portal/`](./portal/): Contains the Route/Endpoint logic for the API. *Actual* function logic should be in [`util/`](./util/).
- [`static/`](./static/): Contains static assets (fonts, img, css) served by the Lambda function.
- [`templates/`](./templates/): Contains all the Jinja2 HTML templates for the API/UI.
- [`tests/`](./tests/README.md): Contains unit tests for the Lambda function, along with a [README](./tests/README.md) to learn more if needed.
- [`util/`](./util/): Contains utility functions used by the Lambda function.
- [`conftest.py`](./conftest.py): Pytest configuration file for the Lambda function tests. There's another one [back one level](../conftest.py) due to pathing/import restrictions. They're automatically imported by pytest for any test that's in/after their respective directories.
- [`main.py`](./main.py): The main entry point for the Lambda function. Setups the Powertools API, and everything after.

## Adding an Application Form to a Lab
Lab configs are stored in [`util/labs/__init__.py`](.util/labs/__init__.py).
To add an application form add the optional parameter `application_questions` to the lab config.
The following describes the available options for defining an application.
```py
application_questions=[
    {
        "name": "user-name",
        "question": "What is your name?",
        "type": "text",
        "rendering_options": "single-line",
        "placeholder": "Type Here",
    },
    {
        "name": "user-story",
        "question": "Why do you want access?",
        "type": "text",
        "rendering_options": "multi-line",
        "placeholder": "Type Here",
    },
    {
        "name": "is-gov",
        "question": "Is this for government use?",
        "type": "checkbox",
    },
    {
        "name": "what-science",
        "question": "What type of science",
        "type": "dropdown",
        "rendering_options": ["SAR", "NISAR"],
    },
]
```
Question parameters
- `name`: The name of the question as it will appear in code
- `question`: The prompt the user will recieve
- `type`: What type of user submission should be rendered
    - text
    - checkbox
    - dropdown
- `rendering_options`: Any additional information used for rendering, is used differently depending on the questions `type`
    - `text` (OPTIONAL)
        - `single-line`: Renders a one line textbox
        - `multi-line`: Renders a large multiline textbox
    - `dropdown`
        - A list of options available to the dropdown, like `["Option 1", "Option 2", ...]`
- `placeholder`(OPTIONAL): The placeholder value for the question.
