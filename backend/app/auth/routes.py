from datetime import timedelta

from app.auth.ratelimit import rate_limiter
from app.auth.schemas import (
    AuthResponse,
    EmailLoginRequest,
    EmailSignupRequest,
    ErrorResponse,
    GoogleLoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    SuccessResponse,
    TokenResponse,
    TokenVerifyRequest,
    UserResponse,
)
from app.auth.security import create_access_token, oauth2_scheme
from app.auth.service import auth_service
from app.config import settings
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    try:
        result = await auth_service.authenticate_user_with_email(
            email=form_data.username, password=form_data.password
        )

        access_token = create_access_token(
            data={"sub": str(result["user"]["_id"])},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        return TokenResponse(access_token=access_token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )


@router.post(
    "/signup/email", response_model=AuthResponse, dependencies=[Depends(rate_limiter)]
)
async def signup_with_email(request: EmailSignupRequest):
    """
    Registers a new user using email, password, and name.
    """
    try:
        result = await auth_service.create_user_with_email(
            email=request.email, password=request.password, name=request.name
        )

        access_token = create_access_token(
            data={"sub": str(result["user"]["_id"])},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        result["user"]["_id"] = str(result["user"]["_id"])

        return AuthResponse(
            access_token=access_token,
            refresh_token=result["refresh_token"],
            user=UserResponse(**result["user"]),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post(
    "/login/email", response_model=AuthResponse, dependencies=[Depends(rate_limiter)]
)
async def login_with_email(request: EmailLoginRequest):
    """
    Authenticates a user using email and password credentials.
    """
    try:
        result = await auth_service.authenticate_user_with_email(
            email=request.email, password=request.password
        )

        access_token = create_access_token(
            data={"sub": str(result["user"]["_id"])},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        result["user"]["_id"] = str(result["user"]["_id"])

        return AuthResponse(
            access_token=access_token,
            refresh_token=result["refresh_token"],
            user=UserResponse(**result["user"]),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.post("/login/google", response_model=AuthResponse)
async def login_with_google(request: GoogleLoginRequest):
    """
    Authenticates or registers a user using a Google OAuth ID token.
    """
    try:
        result = await auth_service.authenticate_with_google(request.id_token)

        access_token = create_access_token(
            data={"sub": str(result["user"]["_id"])},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        result["user"]["_id"] = str(result["user"]["_id"])

        return AuthResponse(
            access_token=access_token,
            refresh_token=result["refresh_token"],
            user=UserResponse(**result["user"]),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(e)}",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refreshes JWT tokens using a valid refresh token.
    """
    try:
        new_refresh_token = await auth_service.refresh_access_token(
            request.refresh_token
        )

        from app.database import get_database

        db = get_database()
        token_record = await db.refresh_tokens.find_one(
            {"token": new_refresh_token, "revoked": False}
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to create new tokens",
            )

        access_token = create_access_token(
            data={"sub": str(token_record["user_id"])},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.post("/token/verify", response_model=UserResponse)
async def verify_token(request: TokenVerifyRequest):
    """
    Verifies an access token and returns the associated user information.
    """
    try:
        user = await auth_service.verify_access_token(request.access_token)

        user["_id"] = str(user["_id"])

        return UserResponse(**user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


@router.post("/password/reset/request", response_model=SuccessResponse)
async def request_password_reset(request: PasswordResetRequest):
    """
    Initiates a password reset process by sending a reset link to the provided email.
    """
    try:
        await auth_service.request_password_reset(request.email)
        return SuccessResponse(
            success=True, message="If the email exists, a reset link has been sent"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset request failed: {str(e)}",
        )


@router.post("/password/reset/confirm", response_model=SuccessResponse)
async def confirm_password_reset(request: PasswordResetConfirm):
    """
    Resets a user's password using a valid password reset token.
    """
    try:
        await auth_service.confirm_password_reset(
            reset_token=request.reset_token, new_password=request.new_password
        )
        return SuccessResponse(
            success=True, message="Password has been reset successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}",
        )
