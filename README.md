# OpenMensa Parser

This script parses the Mensa web pages from [Giro-Web](https://giro-web.com/) and converts them into an OpenMensa feed. It requires a username and password to log in. It is recommended to use a separate account as only one can be logged in at the same time.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/JonatanMGit/openmensa-giro-web.git
    cd giro-web-openmensa-parser
    ```

2. Install the required libraries:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

1. Create a `config.json` file in the root directory with the following content:
    ```json
    {
        "USERNAME": "your_username",
        "PASSWORD": "your_password",
        "BASE_URL": "https://example.com/index.php",
        "TARGET_WEEKS": [
            0,
            1,
            2
        ]
    }
    ```

2. Replace `your_username`, `your_password`, and `https://example.com/index.php` with your actual credentials and the base URL of the Mensa website.

## Usage

1. Run the script:
    ```sh
    python main.py
    ```

2. The OpenMensa feed will be saved to the `output/mensa.xml` file and can be directly provided to the OpenMensa parser.