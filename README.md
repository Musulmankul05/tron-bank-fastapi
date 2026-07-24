# tron-bank-fastapi
tron.bank Migrating to FastAPI for developing pure Core Banking API
***
## Origin
**Modern Core Banking System written in Python with FastAPI (formerly with Django)**  

See [old project with Django](https://github.com/Musulmankul05/tron-bank)

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
