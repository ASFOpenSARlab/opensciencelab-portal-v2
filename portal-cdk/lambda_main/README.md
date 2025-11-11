# Lambda Main

The Core of the project. This function holds all the API/UI logic for the portal itself.

## Directory Structure

- [`data/`](./data/): Contains static data files used by the Lambda function.
- [`portal/`](./portal/): Contains the Route/Endpoint logic for the API. *Actual* function logic should be in [`util/`](./util/).
- [`static/`](./static/): Contains static assets (fonts, img, css) served by the Lambda function.
- [`templates/`](./templates/): Contains all the Jinja2 HTML templates for the API/UI.
- [`tests/`](./tests/README.md): Contains unit tests for the Lambda function, along with a [README](./tests/README.md) to learn more if needed.
- [`util/`](./util/): Contains utility functions used by the Lambda function.
- [`conftest.py`](./conftest.py): Pytest configuration file for the Lambda function tests. There's another one [back one level](../conftest.py) due to pathing/import restrictions. They're automatically imported by pytest for any test that's in/after their respective directories.
- [`main.py`](./main.py): The main entry point for the Lambda function. Setups the Powertools API, and everything after.
