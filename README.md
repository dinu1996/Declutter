# Declutter

Declutter is a powerful, unified Windows system cleaning utility designed to help you manage your installed software and reclaim valuable disk space. 

Unlike the standard Windows "Add/Remove Programs" or "Apps & features" panels which often hide critical system components, split apps across different menus, or fail to cleanly uninstall packages, Declutter intelligently scans and aggregates your installed software from three primary sources into a single, beautiful interface:

1. **Windows Registry (Win32)**: Automatically scans both 32-bit and 64-bit hives across Machine and User contexts to find standard desktop applications, and intelligently un-hides system components like Visual C++ Runtimes.
2. **Microsoft Store (Appx/MSIX)**: Uses native PowerShell cmdlets to properly fetch system packages, runtimes, and frameworks directly from the Store package manager.
3. **Winget Package Manager**: Intelligently deduplicates messy Winget outputs by seamlessly merging Winget's user-friendly display names into their native Appx or Registry counterparts.

It also features a **Large Files** scanner that recursively searches your user directories for massive, space-hogging files, allowing you to delete them quickly.

## Requirements
- Windows 10 or Windows 11
- Administrative Privileges (to properly query the registry and execute uninstallation strings)

## Download & Run
1. Go to the **Releases** tab and download `Declutter.exe`.
2. Run `Declutter.exe`. (A UAC prompt will appear to request admin access).

## Screenshots
*Screenshots coming soon*

## Changelog
- **v1.1**: Custom icon and alternating row colors for improved readability.
- **v1.0**: Initial release featuring unified registry, Appx, and Winget app fetching with large file scanning.

## For Developers
If you want to build Declutter from source, you can use PyInstaller:
```powershell
pip install -r requirements.txt
pyinstaller --noconsole --onefile --uac-admin --icon=icon.ico --add-data "icon.ico;." --name "Declutter" main.py
```
