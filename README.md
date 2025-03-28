# My API Package

A Python client for interacting with XYZ API.

## Installation

```
pip install pitchfork_api
```

## Quick Start

```
from  import APIClient

# Initialize the client
client = APIClient(api_key="your_api_key")

# Make a request
response = client.get_data()
print(response)
```

## Features

- Feature 1
- Feature 2
- Feature 3

## Documentation

For full documentation, visit [our docs](https://your-docs-url.com).

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/pablomaceda3/pitchfork-api.git
cd pitchfork-api

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
