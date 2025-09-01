Py-Easy-Env: The Visual Python Environment Manager
Py-Easy-Env is a simple graphical user interface for managing Python project dependencies and environments without the hassle of complex command-line workflows.

It's designed for developers, data scientists, and students who want a straightforward, visual way to handle project-based dependencies, inspired by modern tools like Poetry but with the simplicity of a GUI.

Key Features
Project-Based Management: Create and switch between isolated projects. Your dependencies for Project A won't interfere with Project B.

Smart Code Scanning: Automatically scan your source code to find all required libraries and add them to your project.

One-Click Dependency Management: Add new packages to your project, and the tool will automatically resolve dependencies, create a lockfile (requirements.txt), and sync your environment.

Intelligent Environment Syncing: When you switch projects, the tool intelligently installs, uninstalls, and updates packages to perfectly match the selected project's requirements.

Self-Healing: If required tools like pip-tools or pipreqs are missing, the app will detect them and offer to install them for you.

Installation & Usage
Getting started is easy.

1. Clone the Repository

git clone [https://github.com/your-username/python-dependency-gui.git](https://github.com/your-username/python-dependency-gui.git)
cd python-dependency-gui

2. Create and Activate a Virtual Environment (Recommended)

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate

3. Run the Application

python app.py

Workflow
Create a Project: Give your project a name (e.g., web-scraper). The app will create a dedicated folder to manage its files.

Add Dependencies:

Use the "Scan Code for Imports" button to automatically find dependencies in your .py files.

Or, manually add a package using the "Add Dependency" input field.

Sync: The tool automatically syncs your environment whenever you add a dependency.

Switch Projects: Simply select another project from the dropdown. The tool will handle the rest, ensuring your environment always matches the selected project.

Contributing
Contributions are welcome! If you have ideas for new features or find a bug, please feel free to open an issue or submit a pull request.

License
This project is licensed under the MIT License.