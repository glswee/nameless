#!/usr/bin/env python3
"""Fix provisioning profiles: add missing keys, inject entitlements and certificates, re-sign."""
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

# Read the developer certificate (DER format)
cert_der_path = os.path.join(CERTS_DIR, 'Public.cer')
with open(cert_der_path, 'rb') as f:
    dev_cert_data = f.read()
print(f"Loaded developer certificate: {len(dev_cert_data)} bytes")

# Extract cert and key for re-signing (use Public.cer + generate a temp key)
# Since p12 uses RC2 which may not be available, use the Public.cer directly
# and create a signing key from it
subprocess.run([
    'openssl', 'x509', '-in', cert_der_path, '-inform', 'DER',
    '-out', '/tmp/cert.pem', '-outform', 'PEM'
], capture_output=True, check=True)

# Generate a key pair for signing if we can't extract from p12
# Try extracting from p12 first
r = subprocess.run([
    'openssl', 'pkcs12', '-in', os.path.join(CERTS_DIR, 'SelfSigned.p12'),
    '-passin', 'pass:', '-nocerts', '-nodes', '-out', '/tmp/key.pem'
], capture_output=True)
if r.returncode != 0:
    # p12 extraction failed, generate a new key
    print("p12 key extraction failed, generating new key...")
    subprocess.run([
        'openssl', 'genrsa', '-out', '/tmp/key.pem', '2048'
    ], capture_output=True, check=True)
    # Re-create a self-signed cert that matches
    subprocess.run([
        'openssl', 'req', '-new', '-x509', '-key', '/tmp/key.pem',
        '-out', '/tmp/cert.pem', '-days', '3650',
        '-subj', '/CN=Fake Developer/O=Fake Team/C=US'
    ], capture_output=True, check=True)
    print("Generated new self-signed cert+key")

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

    # Add DeveloperCertificates (required by codesigningtool)
    d['DeveloperCertificates'] = [dev_cert_data]

    # Build entitlements
    ent = d.get('Entitlements', {})

    # Determine this profile's bundle ID
    ext_bundle = BUNDLE_ID
    for key, bid in PROFILE_BUNDLE_MAP.items():
        if key in fname:
            ext_bundle = bid
            break

    ent['application-identifier'] = TEAM_ID + '.' + ext_bundle
    ent['keychain-access-groups'] = [TEAM_ID + '.' + BUNDLE_ID]
    ent['aps-environment'] = 'development'
    ent['get-task-allow'] = True
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
