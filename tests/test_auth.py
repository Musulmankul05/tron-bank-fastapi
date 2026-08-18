import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import BackupCodesModel, UserModel
from utils.security import hash_backups, hash_password


@pytest.mark.asyncio
async def test_reset_password_rate_limit(
    client: AsyncClient, db_session: AsyncSession
):
    test_user = UserModel(
        first_name="Test",
        last_name="User",
        username="rate_limit_user",
        phone="+996555123456",
        hashed_password=hash_password("old_password123"),
    )
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    backup_code = BackupCodesModel(
        user_id=test_user.id,
        code=hash_backups("abcd-efgh-ijkl-mnop"),
    )
    db_session.add(backup_code)
    await db_session.commit()

    payload = {
        "username": "rate_limit_user",
        "code": "invalid-backup-code",
        "new_pass": "new_secret_123",
        "confirm_pass": "new_secret_123",
        }

    for attempt in range(1, 6):
        response = await client.post("/api/v1/users/reset-password", json=payload)
        assert (
            response.status_code == 400
        ), f"Попытка {attempt}: ожидался 400, получен {response.status_code}"
        assert response.json()["detail"] == "Incorrect code"

    response_blocked = await client.post("/api/v1/users/reset-password", json=payload)
    assert response_blocked.status_code == 429
    assert "Too many failed attempts" in response_blocked.json()["detail"]