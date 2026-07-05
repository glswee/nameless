#!/usr/bin/env python3
"""Fix provisioning profiles: add missing keys, re-sign with security cms -S."""
import plistlib
import subprocess
import uuid
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
PROFILES_DIR = os.path.join(parent_dir, 'fake-codesigning', 'profiles')

# Find a valid signing identity
r = subprocess.run(
    ['security', 'find-identity', '-v', '-p', 'codesigning', 'temp.keychain'],
    capture_output=True, text=True
)
identity = None
for line in r.stdout.splitlines():
    if '"' in line and 'identity' in line.lower():
        identity = line.split('"')[1]
        break

if not identity:
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

print('Using identity: ' + identity)

for fname in sorted(os.listdir(PROFILES_DIR)):
    if not fname.endswith('.mobileprovision'):
        continue
    path = os.path.join(PROFILES_DIR, fname)

    r = subprocess.run(['security', 'cms', '-D', '-i', path], capture_output=True)
    if r.returncode != 0:
        print('SKIP ' + fname + ': cms -D failed')
        continue
    d = plistlib.loads(r.stdout)

    if 'watch' in fname.lower():
        platform = 'WATCH_OS'
    else:
        platform = 'IOS'

    d['Platform'] = platform
    d.setdefault('TimeToLive', 31536000)
    d.setdefault('UUID', str(uuid.uuid4()).upper())
    d.setdefault('Version', 1)

    tmp = '/tmp/_profile_tmp.plist'
    with open(tmp, 'wb') as f:
        plistlib.dump(d, f, fmt=plistlib.FMT_XML)

    r2 = subprocess.run([
        'security', 'cms', '-S', '-k', 'temp.keychain',
        '-N', identity, '-i', tmp, '-o', path
    ], capture_output=True, text=True)

    if r2.returncode != 0:
        print('SKIP ' + fname + ': cms -S failed: ' + r2.stderr[:100])
    else:
        print('Fixed ' + fname + ' -> Platform=' + platform)

    if os.path.exists(tmp):
        os.unlink(tmp)

print('Done.')
