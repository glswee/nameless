#!/usr/bin/env python3
"""Fix provisioning profiles: add missing keys. No re-signing needed - 
the provisioning_profile_tool reads XML plists directly (back door)."""
import plistlib
import subprocess
import uuid
import os

PROFILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'fake-codesigning', 'profiles')

for fname in sorted(os.listdir(PROFILES_DIR)):
    if not fname.endswith('.mobileprovision'):
        continue
    path = os.path.join(PROFILES_DIR, fname)

    # Decode profile
    r = subprocess.run(['security', 'cms', '-D', '-i', path], capture_output=True)
    if r.returncode != 0:
        print(f'SKIP {fname}: cms -D failed')
        continue
    d = plistlib.loads(r.stdout)

    # Determine platform
    if 'watch' in fname.lower():
        platform = 'WATCH_OS'
    else:
        platform = 'IOS'

    # Add missing keys (preserving date types via plistlib)
    d['Platform'] = platform
    d.setdefault('TimeToLive', 31536000)
    d.setdefault('UUID', str(uuid.uuid4()).upper())
    d.setdefault('Version', 1)

    # Write as XML plist directly (no CMS re-signing needed)
    # The provisioning_profile_tool reads XML plists via backdoor path
    with open(path, 'wb') as f:
        plistlib.dump(d, f, fmt=plistlib.FMT_XML)

    print(f'Fixed {fname} -> Platform={platform}')

print(f'Done. Fixed {len([f for f in os.listdir(PROFILES_DIR) if f.endswith(".mobileprovision")])} profiles.')