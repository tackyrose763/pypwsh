# PyPwsh - Python and PowerShell GUI Bridge

`pypwsh.py` is a Python module that leverages Windows PowerShell and XAML/WPF/WinForms to provide simple, native Windows graphical user interface (GUI) elements like dropdown menus, file selectors, and folder browsers. This allows Python scripts to easily integrate rich user input without requiring external Python GUI libraries.

-----

## Prerequisites and Setup

This project uses an embeddable Python distribution that is bundled alongside the main script for portability.

### 1\. Requirements

  * **Project Structure:**
      * The main script is `pypwsh.py`.
      * The embeddable Python distribution is located inside the `rose_core` folder, within a subdirectory named `_pyemb` (i.e., `rose_core\_pyemb`).
  * **Python 3.14 (Embeddable Distribution):** The `_pyemb` directory contains the Python executables. This distribution is assumed to have `pip` and `win32com` pre-installed for automation tasks.
  * **Windows PowerShell:** Available by default on all modern Windows operating systems, it is used by the script to run the GUI functions.

### 2\. Environment Setup

To run `pypwsh.py` from any location, the directory containing the Python executable (`python.exe`) must be added to the user's **PATH** environment variable. The script will automatically find the system's default PowerShell executable.

| Component | Path to Add to User PATH |
| :--- | :--- |
| **Python Executable** | **The full absolute path to the `_pyemb` folder.** |

#### **Steps to Update User Path:**

1.  **Locate the Path:** Navigate to your project folder and find the `_pyemb` subdirectory inside `rose_core`. Copy the **full absolute path** to this folder (e.g., `D:\MyProjects\pypwsh_repo\rose_core\_pyemb`).
2.  **Open Environment Variables:** Search for and open **"Edit the system environment variables"**, then click the **"Environment Variables..."** button.
3.  **Edit User Path:**
      * Under the **"User variables for [username]"** section, select the variable named **`Path`**.
      * Click **"Edit..."**.
4.  **Add Python Path:**
      * In the Edit window, click **"New"**.
      * Paste the **full absolute path** you copied in Step 1.
5.  **Save Changes:** Click **"OK"** on all open windows.
6.  **Verification:** Open a **new** Command Prompt or PowerShell window and type `python --version` to confirm Python runs correctly.

-----

## Module API Reference

The module contains the following functions, all of which execute a temporary PowerShell script to display a GUI and return the user's selection to the Python caller.

### `pypwsh_dropdown()`

Displays an editable dropdown list box populated with a list of options.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `options_list` | `list` | `["", "Rose", "Tulip"]` | The list of strings to populate the dropdown. |
| `allowBlankSubmission` | `bool` | `True` | If `False`, the user cannot confirm an empty string. |
| `removeBlankEntriesFromList` | `bool` | `False` | Removes `""` entries from the initial list display. |
| `allowEditingListItems` | `bool` | `True` | Allows the user to edit a selected item before confirming. |
| **Returns** | `str` | `""` | The confirmed string selection. |

#### Example Usage

```python
from pypwsh import pypwsh_dropdown

# Example 1: Editable list with blank submissions allowed
chosen_item = pypwsh_dropdown(
    options_list=["", "Task A", "Task B", "Task C"],
    allowBlankSubmission=True,
    allowEditingListItems=True
)
print(f"Chosen Item: {chosen_item}")

# Example 2: Non-editable list, blank entries removed
chosen_color = pypwsh_dropdown(
    options_list=["Red", "", "Green", "Blue"],
    removeBlankEntriesFromList=True,
    allowEditingListItems=False
)
print(f"Chosen Color: {chosen_color}")
```

### `pypwsh_filebrowse()`

Displays a graphical file selection dialog.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `initial_path` | `str` | `""` | A starting directory or file path to populate the text box. |
| `filter` | `str` | `"All Files (*.*)|*.*"` | The file type filter string (PowerShell format, e.g., `"Text Files (*.txt)|*.txt"`). |
| `title` | `str` | `"Select a File"` | The title for the file selection window. |
| **Returns** | `str` | `""` | The full path to the selected file, or an empty string on error/cancel. |

#### Example Usage

```python
from pypwsh import pypwsh_filebrowse
import os

# Example 1: Select a specific file type, starting in the user's home directory
home_path = os.path.expanduser("~")
selected_file = pypwsh_filebrowse(
    initial_path=home_path,
    filter="Excel Files (*.xlsx)|*.xlsx|CSV Files (*.csv)|*.csv",
    title="Choose a Data File"
)
print(f"Selected File Path: {selected_file}")
```

### `pypwsh_folderbrowse()`

Displays a graphical folder selection dialog.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `initial_path` | `str` | `""` | A starting directory path to populate the text box. |
| `description` | `str` | `"Select a Folder"` | The description text for the dialog window. |
| `title` | `str` | `"Folder Browser"` | The title for the folder selection window. |
| **Returns** | `str` | `""` | The full path to the selected folder, or an empty string on error/cancel. |

#### Example Usage

```python
from pypwsh import pypwsh_folderbrowse

# Example 1: Select a destination folder
selected_folder = pypwsh_folderbrowse(
    initial_path="C:\\Temp",
    description="Please select the destination directory for output logs.",
    title="Log File Destination"
)
print(f"Selected Folder Path: {selected_folder}")
```
