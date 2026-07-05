#!/usr/bin/env python3
"""Fix provisioning profiles: add missing keys, re-sign with security cms -S."""
import plistlib
import subprocess
import uuid
import os
import sys

PROFILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                            'fake-codesigning', 'profiles')

# Find a valid signing identity in the keychain
r = subprocess.run(
    ['security', 'find-identity', '-v', '-p', 'codesigning', 'temp.keychain'],
    capture_output=True, text=True
)
identity = None
for line in r.stdout.splitlines():
    if 'identity' in line.lower() and '"' in line:
        identity = line.split('"')[1]
        break

if not identity:
    # Try without -p filter
    r = subprocess.run(
        ['security', 'find-identity', '-v', 'temp.keychain'],
        capture_output=True, text=True
    )
    for line in r.stdout.splitlines():
        if '"' in line and 'identity' in line.lower():
            identity = line.split('"')[1]
            break

if not identity:
    print('ERROR: No signing identity found in keychain')
    sys.exit(1)

print(f'Using identity: {identity}')

for fname in sorted(os.listdir(PROFILES_DIR)):
    if not fname.endswith('.mobileprovision'):
        continue
    path = os.path.join(PROFILES_DIR, fname)

    # Decode profile
    r = subprocess.run(['security', 'cms', '-D', '-i', path], capture_output=True)
    if r.returncode != 0:
        print(f'SKIP {fname}: cms -D failed: {r.stderr.decode()[:100]}')
        continue
    d = plistlib.loads(r.stdout)

    # Determine platform
    if 'watch' in fname.lower():
        platform = 'WATCH_OS'
    else:
        platform = 'IOS'

    # Add missing keys
    d['Platform'] = platform
    d.setdefault('TimeToLive', 31536000)
    d.setdefault('UUID', str(uuid.uuid4()).upper())
    d.setdefault('Version', 1)

    # Write modified plist as temp XML, re-sign with security
    tmp = '/tmp/_profile_tmp.plist'
    with open(tmp, 'wb') as f:
        plistlib.dump(d, f, fmt=plistlib.FMT_XML)

    r2 = subprocess.run([
        'security', 'cms', '-S', '-k', 'temp.keychain',
        '-N', identity, '-i', tmp, '-o', path
    ], capture_output=True, text=True)

    if r2.returncode != 0:
        print(f'SKIP {fname}: cms -S failed: {r2.stderr[:100]}')
    else:
        print(f'Fixed {fname} -> Platform={platform}')

    os.unlink(tmp)

print('Done.')