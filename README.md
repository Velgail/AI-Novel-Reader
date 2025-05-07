# Novel LLM Project

## Overview

The Novel LLM Project is a Python-based application designed to interact with large language models (LLMs) and scrape novel data from various sources. The project is structured to facilitate easy development and extension through plugins.

## Directory Structure

The project follows a structured directory layout:

```
novel_llm_project/
├── .vscode/             # VSCode settings (launch.json, settings.json)
├── .github/             # GitHub Actions workflows (future use)
├── core/                # Core functionality modules
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   ├── logger_setup.py  # Logger setup
│   ├── db_schemas.py    # SQLite schema definitions (as Python objects)
│   ├── context_db.py    # Database operation class
│   ├── llm_client.py    # LLM API client
│   ├── plugin_manager.py # Plugin manager
│   └── base_plugin.py   # Base plugin class
├── plugins/             # Feature plugins (subdirectories for each plugin)
│   └── __init__.py
├── scrapers/            # Novel site scraping modules
│   └── __init__.py
├── data/                # Novel data, DB files, dictionaries (gitignore target)
│   └── .gitkeep
├── tests/               # Test code
│   └── __init__.py
├── .gitignore
├── requirements.txt     # Dependency libraries
├── main.py              # Main execution script (CLI entry point)
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/Velgail/AI-Novel-Reader.git
   cd AI-Novel-Reader/novel_llm_project
   ```

2. Create and activate a virtual environment:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your API keys:

   ```sh
   echo "GEMINI_API_KEY=YOUR_API_KEY_HERE" > .env
   ```

### Running the Application

To run the main application, execute:

```sh
python main.py
```

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License

This project is licensed under the Boost Software License 1.0. See the [LICENSE](../LICENSE) file for details.
