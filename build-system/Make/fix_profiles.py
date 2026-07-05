#!/usr/bin/env python3
"""Fix provisioning profiles: add missing Platform key, inject needed entitlements, re-sign."""
import plistlib
import subprocess
import uuid
import os
import datetime
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERTS_DIR = os.path.join(BASE_DIR, 'fake-codesigning', 'certs')
PROFILES_DIR = os.path.join(BASE_DIR, 'fake-codesigning', 'profiles')

# Read configuration
config_path = os.path.join(BASE_DIR, 'appstore-configuration.json')
with open(config_path) as f:
    config = json.load(f)
BUNDLE_ID = config.get('bundle_id', 'app.nameless.messenger')
TEAM_ID = config.get('team_id', 'C67CF9S4VU')

# Map profile filenames to extension bundle IDs
PROFILE_BUNDLE_MAP = {
    'Telegram': BUNDLE_ID,
    'Share': BUNDLE_ID + '.Share',
    'Widget': BUNDLE_ID + '.Widget',
    'NotificationContent': BUNDLE_ID + '.NotificationContent',
    'NotificationService': BUNDLE_ID + '.NotificationService',
    'BroadcastUpload': BUNDLE_ID + '.BroadcastUpload',
    'Intents': BUNDLE_ID + '.SiriIntents',
    'WatchApp': BUNDLE_ID + '.watchkitapp',
    'WatchExtension': BUNDLE_ID + '.watchkitapp.extension',
}

# Extract cert and key from p12
subprocess.run([
    'openssl', 'pkcs12', '-in', os.path.join(CERTS_DIR, 'SelfSigned.p12'),
    '-passin', 'pass:', '-nokeys', '-out', '/tmp/cert.pem'
], capture_output=True, check=True)
subprocess.run([
    'openssl', 'pkcs12', '-in', os.path.join(CERTS_DIR, 'SelfSigned.p12'),
    '-passin', 'pass:', '-nocerts', '-nodes', '-out', '/tmp/key.pem'
], capture_output=True, check=True)

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
    d.setdefault('TeamIdentifier', [TEAM_ID])
    d.setdefault('ApplicationIdentifierPrefix', [TEAM_ID])

    exp = d.get('ExpirationDate')
    if not isinstance(exp, datetime.datetime):
        d['ExpirationDate'] = datetime.datetime(2099, 12, 31, 23, 59, 59)

    # Build entitlements
    ent = d.get('Entitlements', {})

    # Determine this profile's bundle ID
    ext_bundle = BUNDLE_ID  # default
    for key, bid in PROFILE_BUNDLE_MAP.items():
        if key in fname:
            ext_bundle = bid
            break

    ent['application-identifier'] = TEAM_ID + '.' + ext_bundle
    ent['keychain-access-groups'] = [TEAM_ID + '.' + BUNDLE_ID]
    ent['aps-environment'] = 'development'
    ent['get-task-allow'] = True

    # Add application-groups for main app and extensions that need it
    ent['com.apple.security.application-groups'] = ['group.' + BUNDLE_ID]

    d['Entitlements'] = ent

    tmp = '/tmp/_profile_tmp.plist'
    with open(tmp, 'wb') as f:
        plistlib.dump(d, f, fmt=plistlib.FMT_XML)

    subprocess.run([
        'openssl', 'smime', '-sign', '-in', tmp, '-outform', 'DER',
        '-out', path, '-signer', '/tmp/cert.pem',
        '-inkey', '/tmp/key.pem', '-nodetach'
    ], check=True, capture_output=True)
    print('Fixed ' + fname + ' -> Platform=' + platform)
    os.unlink(tmp)

os.unlink('/tmp/cert.pem')
os.unlink('/tmp/key.pem')
print('Done.')
