#!/usr/bin/env python3
"""Fix provisioning profiles: add missing Platform key and re-sign with openssl."""
import plistlib
import subprocess
import uuid
import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERTS_DIR = os.path.join(BASE_DIR, 'fake-codesigning', 'certs')
PROFILES_DIR = os.path.join(BASE_DIR, 'fake-codesigning', 'profiles')

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

    # Ensure ExpirationDate is a datetime
    exp = d.get('ExpirationDate')
    if not isinstance(exp, datetime.datetime):
        d['ExpirationDate'] = datetime.datetime(2099, 12, 31, 23, 59, 59)

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
