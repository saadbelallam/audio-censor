import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from polar.v2026_10.webhooks import validate_event, PolarWebhookVerificationError, WebhookOrderPaidPayload
from svix.webhooks import WebhookVerificationError as SvixWebhookVerificationError, Webhook as SvixWebhook

from app.api.dependencies import PolarDep, UserDep, UserServiceDep
from app.api.schemas.user import CheckoutSessionCreate, TokenData, UserCreate, UserRead
from app.config import settings


router = APIRouter(tags=["User"])


# @router.post("/signup", response_model=UserRead)
# async def register_user(user: UserCreate, service: UserServiceDep) -> UserRead:
#     return await service.add_user(user)


# @router.post("/token", response_model=TokenData)
# async def login_user(
#     service: UserServiceDep,
#     credentials: OAuth2PasswordRequestForm = Depends(),
# ):
#     access_token = await service.generate_token(
#         credentials.username,
#         credentials.password,
#     )
#     if access_token is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model= UserRead)
async def read_current_user(user: UserDep):
    return user

@router.post("/user/checkout")
async def create_checkout(body: CheckoutSessionCreate, user: UserDep, polar: PolarDep):
    
    try:
        checkout = await polar.checkouts.create(
                products = [settings.POLAR_PRODUCT_ID],
                customer_email = user.email,
                external_customer_id = str(user.id),
                metadata = {"user_id": str(user.id)},
                prices = {
                    settings.POLAR_PRODUCT_ID: [
                        {
                            "amount_type": "fixed",
                            "price_amount": int(body.amount * 100),  # Convert to cents
                            "price_currency": "eur",
                        }
                    ]
                }
        )
        return {"checkout_url": checkout.url}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout: {str(e)}",
        )

    
@router.post("/webhooks/polar", include_in_schema=False)
async def handle_polar_webhook(request: Request, service: UserServiceDep):
    try:
        event = validate_event(
            body=await request.body(),
            headers=dict(request.headers),
            secret=settings.POLAR_WEBHOOK_SECRET
        )


        if isinstance(event, WebhookOrderPaidPayload):
            
            user_id = event.data.metadata.get("user_id")
            if user_id is not None:
                await service.add_credits(UUID(user_id), event.data.subtotal_amount)
    except PolarWebhookVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook signature",
        )

@router.post("/webhooks/propelauth", include_in_schema=False, status_code=status.HTTP_202_ACCEPTED)
async def handle_propelauth_webhook(request: Request, service: UserServiceDep):
    wh = SvixWebhook(settings.PROPELAUTH_WEBHOOK_SECRET)
    body = await request.body()

    try:
        wh.verify(body, dict(request.headers))
    except SvixWebhookVerificationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature",
        )

    event_data = json.loads(body)
    event_type = event_data.get("event_type")
    if event_type == "user.created":
        print(event_data)
        await service.add_user(event_data)

    return {"received": True}