# GateAssignmentDirector

A bridge between [SayIntentions AI](https://sayintentions.ai) and [GSX](https://www.fsdreamteam.com/products_gsxpro.html) gate assignment for Microsoft Flight Simulator 2020.  
  
A shoutout is given to [Fenix2GSX](https://github.com/Fragtality/Fenix2GSX). Although zero source code or internal algorithms have been taken or appropriated from Fenix2GSX, the project was helpful to garner initial understanding of controling GSX through LVAR.

## What it does

Automatically assigns gates in GSX based on gate information from SayIntentions AI flight plans. Monitors flight data, parses gate assignments, and navigates GSX menus to set the correct gate.

## Requirements

- Microsoft Flight Simulator 2020 with SimConnect
- [GSX (Ground Services X)](https://www.fsdreamteam.com/products_gsxpro.html)
- [SayIntentions AI](https://sayintentions.ai)
- Python 3.8+ (for development only)

## Installation

### For End Users (Recommended)

1. Download the latest `GateAssignmentDirector.exe` from the [Releases page](https://github.com/Teufelsstern/GateAssignmentDirector/releases)
2. Extract the executable to a folder of your choice (e.g., `C:\GateAssignmentDirector\`)
3. Run `GateAssignmentDirector.exe` - the application will create a default `config.yaml` file on first launch
4. Ensure Microsoft Flight Simulator 2020, GSX Pro, and SayIntentions AI are installed and running

### For Developers

1. Clone this repository:
   ```bash
   git clone https://github.com/Teufelsstern/GateAssignmentDirector.git
   cd GateAssignmentDirector
   ```
2. Install Python 3.8 or higher
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Usage

### Initial Setup

1. **Configure your SayIntentions API Key:**
   - Open the application, go to the "Config" tab, and enter your API key there (recommended for both .exe users and developers)
   - Alternatively, developers can edit `GateAssignmentDirector/config.yaml` directly and replace `YOUR_API_KEY_HERE` with your actual SayIntentions API key
   - If you don't have an API key, get it from the SayIntentions pilot portal

2. **Verify GSX Installation:**
   - The default GSX menu paths should work automatically:
     ```
     C:\Program Files (x86)\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu
     C:\Program Files\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu
     ```
   - If GSX is installed in a different location, update the `menu_file_paths` in the Config tab (for .exe users) or in `config.yaml` (for developers)

### Running the Application

**Using the GUI (Recommended)**
1. Run `GateAssignmentDirector.exe` (or `python main.py` for developers)
2. The application will start with the main window visible. You can configure it to minimize to system tray and/or stay always on top via the Config tab
3. Go to the "Config" tab to verify settings and enter your API key
4. Go to the "Monitor" tab and click "Start Monitoring"
5. The application will now automatically assign gates when SayIntentions flight data is detected

### Configuration Options

The `config.yaml` file contains all application settings. **For .exe users, edit these through the Config tab in the UI.** For developers, the config file is located at `GateAssignmentDirector/config.yaml`.

Available configuration options:

- **`SI_API_KEY`**: Your SayIntentions API key (default: `YOUR_API_KEY_HERE`)
- **`menu_file_paths`**: List of GSX menu file locations (usually auto-detected)
- **`sleep_short`**: Short delay between menu operations in seconds (default: `0.1`)
- **`sleep_long`**: Long delay between menu operations in seconds (default: `0.3`)
- **`ground_check_interval`**: How often to check if aircraft is on ground in seconds (default: `1.0`)
- **`aircraft_request_interval`**: How often to request aircraft data from SimConnect in seconds (default: `2.0`)
- **`max_menu_check_attempts`**: Number of attempts to verify menu changes (default: `4`)
- **`logging_level`**: Logging verbosity - `DEBUG` for detailed logs, `INFO` for normal operation (default: `DEBUG`)
- **`logging_format`**: Format string for log messages (default: `%(asctime)s - %(levelname)s - %(message)s`)
- **`logging_datefmt`**: Date/time format for log timestamps (default: `%H:%M:%S`)
- **`default_airline`**: Default airline selection in GSX (default: `GSX`)

### Troubleshooting

- **Gates aren't being assigned:** Make sure the GSX toolbar button is active/turned on in MSFS (the GSX window can be minimized, but the add-on must be enabled)
- **SayIntentions data not detected:** Check that the flight data file exists at `C:\Users\[YourUsername]\AppData\Local\SayIntentionsAI\flight.json`
- **Persistent issues:** Try restarting GSX (use "Restart Couatl" from GSX menu). If that doesn't help, restart the flight simulator. If problems persist and it has worked before, restart your computer
- **Reporting bugs:** Always save the log file and attach it when reporting issues (use the "Save Logs" button in the Logs tab)

## Features

- **Automatic gate parsing** from SayIntentions flight data
- **Intelligent fuzzy matching** with component-based weighted scoring to handle variations in gate naming formats
- **Menu navigation automation** for hands-free GSX gate selection
- **Airport gate mapping and caching** for improved performance
- **Gate management window** for manual gate editing
  - Rename terminals and reorganize gate assignments
  - Bulk prefix/suffix operations for gate identifiers
  - Alphanumeric sorting and filtering
- **Success confirmation** via GSX tooltip monitoring for reliable assignment verification
- **Comprehensive logging** with configurable verbosity levels
- **Modern GUI with system tray integration**
  - Real-time flight monitoring display
  - Live configuration editing with save/reload
  - Status indicators and event logging
  - Always-on-top window option
  - Airport override for manual control
- **Full test suite** with 340+ unit tests ensuring reliability (dev only)

## Documentation

📚 **[Complete Documentation](docs/README.md)**

### User Manual
- **[Gate Management Window](docs/user-manual/gate-management-window.md)** - Edit and reorganize airport gates

*More guides coming soon: Installation, Configuration, Basic Usage, Troubleshooting*

### Developer Documentation
- **[Architecture](docs/agents/architecture.md)** - System design and components
- **[Data Structures](docs/agents/data-structures.md)** - JSON formats and parsing
- **[Testing Guide](docs/agents/testing.md)** - Test patterns and fixtures
- **[UI System](docs/agents/ui-system.md)** - Color palette and styling

## Testing

Run the test suite (developers only):
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
| CTkToolTip | CC0-1.0 | https://github.com/Akascape/CTkToolTip |
| Pillow | HPND | https://pillow.readthedocs.io/ |
| pystray | GPL-3.0 | https://github.com/moses-palmer/pystray |

All dependencies are compatible with AGPL-3.0.

## Project Status

This is a foundation project meant to be built upon and extended by the community. It's provided as-is with no commitment to ongoing maintenance, support, or pull request reviews. Feel free to fork and adapt it to your needs, adhering to the principles of free software under AGPL-3.0 (including added terms).

## Disclaimer

This project is an independent bridge/integration tool. No ownership or affiliation is claimed with SayIntentions AI or GSX (Ground Services X). All trademarks and product names belong to their respective owners.

## License

AGPL-3.0 (including added terms) - Free to use, modify, and redistribute.
