# Swiftsync - Subprocess Management with Python

Swiftsync is an ultra simple Python application designed to manage multiple subprocesses using tkinter for the user interface and multiprocessing for handling the subprocesses. This project provides a framework for running various modules concurrently, making it suitable for tasks like monitoring and automation.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features
- Launch and manage multiple subprocesses concurrently.
- User-friendly tkinter-based graphical user interface.
- Real-time status updates for each subprocess.
- Log messages for monitoring and debugging.

## Prerequisites
- Python 3.x
- tkinter library (usually included in Python's standard library)
- No additional external dependencies are required.

## Installation
1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/yourusername/swiftsync.git
    ```

2. Change to the project directory:

    ```bash
    cd swiftsync
    ```

3. Run the application:

    ```bash
    python swiftsync.py
    ```

## Usage
1. Upon running the application, you will be presented with a GUI window.
2. The GUI displays the current modules loaded and their statuses.
3. Modules are loaded from the `processes` directory and should follow a specific structure. (See example within the files)

### Adding a New Module
1. Create a new Python module within the `processes` directory. You can use existing modules as templates.
2. Ensure the module contains a `main` function that accepts a `Queue` as an argument for communicating with the main application.
3. Add the module to the `obj.addService("module_name", row)` section in the main script (`swiftsync.py`), specifying the module's name and the row in the GUI where it should appear.
4. It may be necessary to import the sub process into the main.py file if the end goal is an EXE file. 

### Monitoring
- The GUI updates in real-time, displaying the status of each module.
- Logs are written to `swiftsync.log` for monitoring and debugging purposes.

## Contributing
Contributions are welcome! If you have suggestions, bug reports, or would like to contribute code, please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix: `git checkout -b feature-name`
3. Make your changes and commit them: `git commit -m 'Description of your changes'`
4. Push to the branch: `git push origin feature-name`
5. Create a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Homepage
Visit homepage at [https://www.killgorack.com/PX4/index.php?ap=hme&cn=hme](https://www.killgorack.com/PX4/index.php?ap=hme&cn=hme)

![screencapture](https://github.com/KillGorack/Swiftsinc/assets/35109859/359b3a59-4f78-4083-97ac-4d3f2356e9a2)
