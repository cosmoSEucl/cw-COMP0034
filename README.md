# COMP0034 Coursework 1 and 2

This repository contains the practicals for the COMP0034 Coursework 1 and 2.

## Instructions for using this repository

1.  Fork this repository to your own GitHub account.
2.  Clone the forked repository to your local machine (e.g., in VS Code or PyCharm).
3.  Update the repository using the 'Sync fork' button in GitHub to check for changes, if it is out of date then select the 'Update branch' button.

## Instructions and code files for Coursework 1

Before running the code, create a Python virtual environment and download the required libraries using `pip install -r requirements.txt` and `pip install -e .`. The `pip install -e .` command installs the project in editable mode, allowing changes to the code to be immediately reflected without reinstallation.

The `code` folder contains the py files for section 1 and 2.

1.  `app.py`: Contains the Dash app code that can be run in development mode. The HTML layout includes 6 different charts that are dynamically generated. Each chart interacts with the dataset data (see xlsx file within the `data` folder).
2.  `test_app.py`: Contains the 6 browser-driven tests required for section 2. These tests simulate user interactions with the Dash app in the browser, such as clicking dropdowns and checking visualization updates. To run the tests, navigate to the `code` directory and use the command `python -m pytest`. For instance, I used `cd "/Users/comecosmolabautiere/Desktop/Year 3/Modules /Term 2/Software Engineering II/Coursework/comp0034-cw-cosmoSEucl/coursework1/code"`. To ensure the tests run successfully, the Dash app should be running in a separate terminal instance.

The `data` folder contains the xlsx files used in this coursework. All files were downloaded from the [GLA Grants website](https://data.london.gov.uk/dataset/gla-grants-data).

The `report` folder contains the md file with the coursework essay and any PNG images featured in `coursework1.md`.

Flake8 can be run on the code files using the following commands:

*   `flake8 app.py`
*   `flake8 test_app.py`

See GitHub repository [here](https://github.com/ucl-comp0035/comp0034-cw-cosmoSEucl.git). 


Passwords for coursework 2:
- Admin: username *admin1* and password *admin1234* 
- User: username *user1* and password *user_password*

python -m pytest --cov