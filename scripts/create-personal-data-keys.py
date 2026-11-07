"""Create keys once. Never print or overwrite them; back them up securely."""
import os, secrets, sys
from cryptography.fernet import Fernet
with open(os.open(sys.argv[1], os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600), 'w') as f:
    f.write('PII_ENCRYPTION_KEYS='+Fernet.generate_key().decode()+'\nPII_LOOKUP_KEY='+secrets.token_urlsafe(48)+'\n')
print('Created private key file. Keep it outside Git and back it up securely.')
