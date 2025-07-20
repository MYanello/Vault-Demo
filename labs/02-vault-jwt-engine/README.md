# Lab 02: Vault JWT Engine

Now we'll set up Vault's Transit engine to sign JWTs for us:
```bash
./labs/02-vault-jwt-engine/transit-engine.sh
```

Then we have our Auth service which Vault trusts handled the validation of the payload. In this case we call it Django since users can log in to Django and form the payload there.
This script does the following:
1. Forms a jwt signing input from the header and payload
2. Requests our Vault instance to sign it using the Django private key
3. Requests the public key for our Django key
4. Validates our fully formed jwt header is valid based on the public key given by Vault

To run through the above we run 
```bash
python ./labs/02-vault-jwt-engine/jwt-issue.py
```
and press enter to step through the program.

One critical thing to notice here is that the private key has never been requested or left the safety of our Vault. We know we can trust the JWT requester to form a legit payload, so our end service simply needs to get the public key and validate the signature. We can provide further validation on the payload such as making sure it isn't expired at the service. The important thing is that we know that what is in the payload is trusted.