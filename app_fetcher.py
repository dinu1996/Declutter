import winreg
import subprocess
import json
import os
import shutil

class AppFetcher:
    @staticmethod
    def get_registry_apps():
        apps = []
        keys_to_check = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_READ),
        ]

        seen = set()

        for hive, key_path, access in keys_to_check:
            try:
                with winreg.OpenKey(hive, key_path, 0, access) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                except FileNotFoundError:
                                    continue
                                
                                try:
                                    system_component = winreg.QueryValueEx(subkey, "SystemComponent")[0]
                                    if system_component == 1:
                                        disp_lower = str(display_name).lower()
                                        if "visual c++" not in disp_lower and "webview2" not in disp_lower and "wireless" not in disp_lower:
                                            continue
                                except FileNotFoundError:
                                    pass

                                try:
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                except FileNotFoundError:
                                    version = "Unknown"

                                try:
                                    install_date = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                except FileNotFoundError:
                                    install_date = "Unknown"

                                uninstall_string = None
                                quiet_uninstall = None
                                try:
                                    quiet_uninstall = winreg.QueryValueEx(subkey, "QuietUninstallString")[0]
                                except FileNotFoundError:
                                    pass
                                
                                try:
                                    uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                except FileNotFoundError:
                                    pass

                                final_uninstall = quiet_uninstall if quiet_uninstall else uninstall_string
                                if not final_uninstall:
                                    continue
                                
                                # Sometimes paths have quotes or arguments
                                if display_name in seen:
                                    continue
                                seen.add(display_name)

                                apps.append({
                                    "name": display_name,
                                    "version": str(version),
                                    "date": str(install_date),
                                    "source": "Registry",
                                    "uninstall_cmd": final_uninstall,
                                    "type": "cmd"
                                })
                        except Exception:
                            continue
            except Exception:
                continue

        return apps

    @staticmethod
    def get_appx_packages():
        apps = []
        try:
            cmd = [
                'powershell', '-NoProfile', '-Command', 
                '@(Get-AppxPackage | ForEach-Object { $pkg = $_; $manifest = Get-AppxPackageManifest $_ -ErrorAction SilentlyContinue; [PSCustomObject]@{ Name=$pkg.Name; DisplayName=$manifest.Package.Properties.DisplayName; Version=$pkg.Version; PackageFullName=$pkg.PackageFullName } }) | ConvertTo-Json -Compress'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                import re
                for item in data:
                    raw_name = item.get("Name", "Unknown")
                    disp_name = item.get("DisplayName", "")
                    
                    is_guid = bool(re.match(r'^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$', str(disp_name).strip('{}')))
                    is_resource = str(disp_name).startswith("ms-resource:")
                    
                    if not disp_name or is_guid or is_resource:
                        final_name = raw_name
                    else:
                        final_name = disp_name

                    # Filter out apps where Name is a pure GUID
                    if bool(re.match(r'^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$', str(final_name).strip('{}'))):
                        continue

                    apps.append({
                        "name": final_name,
                        "raw_name": raw_name,
                        "version": item.get("Version", "Unknown"),
                        "date": "Unknown",
                        "source": "MS Store",
                        "uninstall_cmd": item.get("PackageFullName", ""),
                        "type": "appx"
                    })
        except Exception as e:
            print(f"Error fetching Appx: {e}")
        return apps

    @staticmethod
    def get_choco_apps():
        apps = []
        if not shutil.which("choco"):
            return apps
        try:
            cmd = ['choco', 'list', '-l', '-r']
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        apps.append({
                            "name": name,
                            "version": version,
                            "date": "Unknown",
                            "source": "Chocolatey",
                            "uninstall_cmd": name,
                            "type": "choco"
                        })
        except Exception:
            pass
        return apps

    @staticmethod
    def get_scoop_apps():
        apps = []
        scoop_dir = os.path.expanduser('~/scoop/apps')
        if not os.path.isdir(scoop_dir):
            return apps
        try:
            for item in os.listdir(scoop_dir):
                if item.lower() == 'scoop':
                    continue
                app_path = os.path.join(scoop_dir, item)
                if os.path.isdir(app_path):
                    # version is usually the folder inside, or we can check manifest.json
                    current_path = os.path.join(app_path, 'current')
                    version = "Unknown"
                    if os.path.exists(current_path):
                        try:
                            manifest_path = os.path.join(current_path, 'manifest.json')
                            if os.path.exists(manifest_path):
                                with open(manifest_path, 'r', encoding='utf-8') as f:
                                    manifest = json.load(f)
                                    version = manifest.get('version', 'Unknown')
                        except Exception:
                            pass
                    apps.append({
                        "name": item,
                        "version": version,
                        "date": "Unknown",
                        "source": "Scoop",
                        "uninstall_cmd": item,
                        "type": "scoop"
                    })
        except Exception:
            pass
        return apps

    @classmethod
    def get_winget_apps(cls, reg_apps=None, appx_apps=None):
        apps = []
        if not shutil.which("winget"):
            return apps
        if reg_apps is None:
            reg_apps = cls.get_registry_apps()
        if appx_apps is None:
            appx_apps = cls.get_appx_packages()
        try:
            cmd = ['winget', 'list', '--accept-source-agreements']
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                header_line = None
                header_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('Name') and 'Id' in line and 'Version' in line:
                        header_line = line
                        header_idx = i
                        break
                if header_line:
                    id_idx = header_line.find('Id')
                    version_idx = header_line.find('Version')
                    available_idx = header_line.find('Available')
                    source_idx = header_line.find('Source')

                    for line in lines[header_idx+2:]:
                        if not line.strip(): continue
                        name = line[:id_idx].strip()
                        app_id = line[id_idx:version_idx].strip()
                        
                        # version bounds depend on whether Available or Source is present
                        end_bound = available_idx if available_idx != -1 else (source_idx if source_idx != -1 else len(line))
                        version = line[version_idx:end_bound].strip()
                        
                        if source_idx != -1:
                            source_val = line[source_idx:].strip()
                            if source_val.lower() != 'winget' and not app_id.upper().startswith("MSIX\\"):
                                continue
                        else:
                            if not app_id.upper().startswith("MSIX\\"):
                                continue

                        if name and app_id:
                            if app_id.upper().startswith("ARP\\"):
                                continue

                            if app_id.upper().startswith("MSIX\\"):
                                matched_appx = None
                                for a_app in appx_apps:
                                    if a_app['name'].lower() == name.lower() or (a_app.get('raw_name') and a_app['raw_name'].lower() in app_id.lower()):
                                        matched_appx = a_app
                                        break
                                
                                if matched_appx:
                                    if matched_appx['name'] == matched_appx.get('raw_name') or matched_appx['name'].startswith('ms-resource:'):
                                        matched_appx['name'] = name
                                    continue
                            else:
                                if "." not in app_id:
                                    continue
                                
                            # Must not exist in registry
                            is_in_reg = False
                            for r_app in reg_apps:
                                r_name_lower = r_app['name'].lower()
                                w_name_lower = name.lower()
                                if len(r_name_lower) > 5 and len(w_name_lower) > 5:
                                    if r_name_lower == w_name_lower or r_name_lower in w_name_lower or w_name_lower in r_name_lower:
                                        is_in_reg = True
                                        break
                            if is_in_reg:
                                continue
                                
                            apps.append({
                                "name": name,
                                "version": version,
                                "date": "Unknown",
                                "source": "Winget",
                                "uninstall_cmd": app_id,
                                "type": "winget"
                            })
        except Exception:
            pass
        return apps

    @classmethod
    def get_all_apps(cls):
        apps = []
        reg_apps = cls.get_registry_apps()
        appx_apps = cls.get_appx_packages()
        
        apps.extend(reg_apps)
        apps.extend(appx_apps)
        apps.extend(cls.get_choco_apps())
        apps.extend(cls.get_scoop_apps())
        apps.extend(cls.get_winget_apps(reg_apps, appx_apps))
        
        # Sort alphabetically
        apps.sort(key=lambda x: x['name'].lower())
        return apps

    @staticmethod
    def uninstall_app(app_info):
        try:
            app_type = app_info.get('type')
            cmd = app_info.get('uninstall_cmd')
            
            if app_type == 'cmd':
                result = subprocess.run(cmd, shell=True)
                if result.returncode == 0:
                    return True, "Uninstalled successfully."
                else:
                    return False, f"Uninstaller exited with code {result.returncode}"
            elif app_type == 'appx':
                raw_name = app_info.get('raw_name', cmd.split('_')[0])
                ps_cmd = ['powershell', '-NoProfile', '-Command', f'Remove-AppxPackage -Package "{cmd}" -AllUsers -ErrorAction Stop']
                result = subprocess.run(ps_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                if result.returncode == 0:
                    return True, "Uninstalled successfully."
                else:
                    prov_cmd = ['powershell', '-NoProfile', '-Command', f'Get-AppxProvisionedPackage -Online | Where-Object DisplayName -eq "{raw_name}" | Remove-AppxProvisionedPackage -Online -ErrorAction Stop']
                    result_prov = subprocess.run(prov_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if result_prov.returncode == 0:
                        return True, "Uninstalled provisioned package successfully."
                    else:
                        err1 = result.stderr.strip() or result.stdout.strip()
                        err2 = result_prov.stderr.strip() or result_prov.stdout.strip()
                        return False, f"Normal uninstall:\n{err1}\n\nProvisioned uninstall:\n{err2}"
            elif app_type == 'choco':
                c_cmd = ['choco', 'uninstall', cmd, '-y']
                result = subprocess.run(c_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    return True, "Uninstalled successfully."
                else:
                    return False, result.stderr.strip() or result.stdout.strip()
            elif app_type == 'scoop':
                s_cmd = ['scoop', 'uninstall', cmd]
                result = subprocess.run(s_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    return True, "Uninstalled successfully."
                else:
                    return False, result.stderr.strip() or result.stdout.strip()
            elif app_type == 'winget':
                w_cmd = ['winget', 'uninstall', '--id', cmd, '--accept-source-agreements']
                result = subprocess.run(w_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    return True, "Uninstalled successfully."
                else:
                    return False, result.stderr.strip() or result.stdout.strip()
            
            return False, "Unknown app type."
        except Exception as e:
            return False, str(e)
