from propelauth_fastapi import init_auth

from app.config import settings

if __name__ == "__main__":
    auth = init_auth(
        settings.PROPELAUTH_AUTH_URL,
        settings.PROPELAUTH_API_KEY,
    )

    response = auth.create_access_token(
        user_id="c9671e1b-7162-4163-af92-ebdc93d1be13",
        duration_in_minutes=60*24,  # 1 day
    )
    print("Generated user token:", response.access_token)