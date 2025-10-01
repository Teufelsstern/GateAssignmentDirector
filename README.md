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

1. Download the latest `GateAssignmentDirector.exe` from the [Releases page](https://github.com/your-username/GateAssignmentDirector/releases)
2. Extract the executable to a folder of your choice (e.g., `C:\GateAssignmentDirector\`)
3. Run `GateAssignmentDirector.exe` - the application will create a default `config.yaml` file on first launch
4. Ensure you have Microsoft Flight Simulator 2020, GSX Pro, and SayIntentions AI installed and running

## Usage

### Initial Setup
1. **Configure your SayIntentions API Key:**
   - Open the application UI or edit `config.yaml` directly  
   - Locate the `SI_API_KEY` field and replace `YOUR_API_KEY_HERE` with your actual SayIntentions API key
   - If you don't have an API key, contact SayIntentions AI for access

2. **Verify GSX Installation:**
   - The default GSX menu paths should work automatically:
     ```
     C:\Program Files (x86)\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu
     C:\Program Files\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu
     ```
   - If GSX is installed in a different location, update the `menu_file_paths` in `config.yaml`

### Running the Application

**Option 1: Using the GUI (Recommended)**
1. Run `GateAssignmentDirector.exe`
2. The application will start in the system tray
3. Open the main window by clicking the system tray icon
4. Go to the "Config" tab to verify settings and enter your API key
5. Go to the "Monitor" tab and click "Start Monitoring"
6. The application will now automatically assign gates when SayIntentions flight data is detected

**Option 2: Command Line Interface**
- Use `GateAssignmentDirector/cli_gsx.py` for manual gate assignments via command line

### Configuration Options
The `config.yaml` file contains various settings:

- `SI_API_KEY`: Your SayIntentions API key
- `menu_file_paths`: GSX menu file locations (usually auto-detected)
- `sleep_short`, `sleep_long`: Timing delays for menu operations
- `ground_check_interval`: How often to check if aircraft is on ground
- `max_menu_check_attempts`: Number of attempts to verify menu changes
- `logging_level`: Set to DEBUG for detailed logs, INFO for normal operation
- `default_airline`: Default airline selection (default: "GSX")

### Troubleshooting
- If gates aren't being assigned, make sure the GSX toolbar button is active/turned on in MSFS (the GSX window can be minimized, but the add-on must be enabled)
- If problems persist, try restarting SayIntentions AI first before other components
- Ensure the aircraft is on the ground when gate assignment is attempted
- Check log files for error messages and detailed operation information
- If menu navigation fails repeatedly after trying the above steps, then try restarting the flight simulator

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

## Dependencies

For licensing compliance and transparency, below are the open-source libraries used in this project:

| Library | License | Repository/Documentation |
|---------|---------|--------------------------|
| PyYAML | MIT | https://pyyaml.org/ |
| rapidfuzz | MIT | https://github.com/maxbachmann/RapidFuzz |
| requests | Apache 2.0 | https://requests.readthedocs.io/ |
| Python-SimConnect | AGPL-3.0 | https://github.com/odwdinc/Python-SimConnect |
| CustomTkinter | MIT | https://github.com/TomSchimansky/CustomTkinter |
| Pillow | HPND | https://pillow.readthedocs.io/ |
| pystray | GPL-3.0 | https://github.com/moses-palmer/pystray |

All dependencies are compatible with GPL-3.0.

## Project Status

This is a foundation project meant to be built upon and extended by the community. It's provided as-is with no commitment to ongoing maintenance, support, or pull request reviews. Feel free to fork and adapt it to your needs, adhering to the principles of free software under GPL-3.0.

## Disclaimer

This project is an independent bridge/integration tool. No ownership or affiliation is claimed with SayIntentions AI or GSX (Ground Services X). All trademarks and product names belong to their respective owners.

## License

GPL-3.0 - Free to use, modify, and redistribute.