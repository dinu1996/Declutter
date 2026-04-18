# Declutter

Declutter is a powerful, unified Windows system cleaning utility designed to help you manage your installed software and reclaim valuable disk space. 

Unlike the standard Windows "Add/Remove Programs" or "Apps & features" panels which often hide critical system components, split apps across different menus, or fail to cleanly uninstall packages, Declutter intelligently scans and aggregates your installed software from three primary sources into a single, beautiful interface:

1. **Windows Registry (Win32)**: Automatically scans both 32-bit and 64-bit hives across Machine and User contexts to find standard desktop applications, and intelligently un-hides system components like Visual C++ Runtimes.
2. **Microsoft Store (Appx/MSIX)**: Uses native PowerShell cmdlets to properly fetch system packages, runtimes, and frameworks directly from the Store package manager.
3. **Winget Package Manager**: Intelligently deduplicates messy Winget outputs by seamlessly merging Winget's user-friendly display names into their native Appx or Registry counterparts.

It also features a **Large Files** scanner that recursively searches your user directories for massive, space-hogging files, allowing you to delete them quickly.

## Requirements
- Windows 10 or Windows 11
- Python 3.10+
- Administrative Privileges (to properly query the registry and execute uninstallation strings)

## How to Run

### Run from Source
1. Clone the repository and install requirements (e.g. `pip install customtkinter`).
2. Run `main.py` with Administrator privileges.

### Build Executable
Declutter can be compiled into a single, standalone executable using PyInstaller.
```powershell
pyinstaller --noconsole --onefile --uac-admin --name "Declutter" main.py
```
This command automatically bakes in the UAC Administrator prompt and outputs `Declutter.exe` into the `dist` folder.
