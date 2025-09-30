# GateAssignmentDirector

A bridge between [SayIntentions AI](https://sayintentions.ai) and [GSX](https://www.fsdreamteam.com/products_gsxpro.html) gate assignment for Microsoft Flight Simulator 2020.

## What it does

Automatically assigns gates in GSX based on gate information from SayIntentions AI flight plans. Monitors flight data, parses gate assignments, and navigates GSX menus to set the correct gate.

## Requirements

- Python 3.8+
- Microsoft Flight Simulator 2020 with SimConnect
- [GSX (Ground Services X)](https://www.fsdreamteam.com/products_gsxpro.html)
- [SayIntentions AI](https://sayintentions.ai)

## Installation

TODO: Installation instructions coming soon

## Usage

TODO: Usage instructions coming soon

## Features

- Automatic gate parsing from SayIntentions flight data
- Fuzzy matching for gate assignments
- Menu navigation automation
- Airport gate mapping and caching
- Comprehensive logging
- Full test suite with 106+ unit tests

## Testing

Run the test suite:
```bash
python -m unittest discover tests
```

## Project Status

This is a foundation project meant to be built upon and extended by the community. It's provided as-is with no commitment to ongoing maintenance, support, or pull request reviews. Feel free to fork and adapt it to your needs, adhering to the principles of free software under GPL-3.0.

## Disclaimer

This project is an independent bridge/integration tool. No ownership or affiliation is claimed with SayIntentions AI or GSX (Ground Services X). All trademarks and product names belong to their respective owners.

## License

GPL-3.0 - Free to use, modify, and redistribute.