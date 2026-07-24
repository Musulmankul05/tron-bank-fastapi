# tron-bank-fastapi
tron.bank Migrating to FastAPI for developing pure Core Banking API
***
## Origin
**Modern Core Banking System written in Python**

## Features
* Atomic transactions
* Sending cash via phone number or username
* Fixed race conditions while bunch transaction
* Digital Signature encrypted to Base64
* Fixed N + 1 Query problem
* 2FA Authentication using TOTP (Time-based One-Time Password)
* Backup codes in case when User lost his password or authenticator
* _Authentication with Mail (may not implemented)_

## Stacks
* FastAPI (Pydantic)
* SQLAlchemy
* PostgreSQL (asyncpg)
* PyOTP
