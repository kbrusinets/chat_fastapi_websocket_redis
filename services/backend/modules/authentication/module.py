from datetime import datetime, UTC
from typing import Tuple, Optional, Any

from services.app.logger import logger
from services.db.models import TokenBlacklist

import bcrypt
import jwt
from jwt import PyJWTError
from sqlalchemy import select

from services.app.schemas import Cookie, TokenData, TokenType
from services.app.settings import settings
from services.backend.exceptions import BackendServiceException
from services.backend.modules.base import ModuleWithDb
from services.db.models import User


class AuthenticationModule(ModuleWithDb):
    async def login(self, email: str, password: str) -> Tuple[User, Cookie, Cookie]:
        user = await self._authenticate_user(email=email, password=password)
        if not user:
            raise BackendServiceException('Invalid authentication credentials.')

        access_token_val = await self._create_token(data={'sub': str(user.id)}, token_type=TokenType.ACCESS)
        access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        refresh_token_val = await self._create_token(data={'sub': str(user.id)}, token_type=TokenType.REFRESH)
        refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        access_token = Cookie(
            key='access_token',
            value=access_token_val,
            httponly=True,
            secure=True,
            samesite='strict',
            max_age=access_max_age
        )

        refresh_token = Cookie(
            key='refresh_token',
            value=refresh_token_val,
            httponly=True,
            secure=True,
            samesite='strict',
            max_age=refresh_max_age
        )

        return user, access_token, refresh_token

    async def refresh_access(self, refresh_token: str, cur_access_token: str) -> Cookie:
        user_data = await self._verify_token(
            token=refresh_token, expected_token_type=TokenType.REFRESH)
        if not user_data:
            raise BackendServiceException('Invalid refresh token.')

        access_token = await self._create_token(data={'sub': str(user_data.user_id)}, token_type=TokenType.ACCESS)
        if cur_access_token:
            await self._blacklist_token(cur_access_token)
        access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        access_token = Cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='strict',
            max_age=access_max_age
        )

        return access_token

    async def get_current_user(self, token: str) -> User | None:
        token_data = await self._verify_token(token, TokenType.ACCESS)
        if token_data is None:
            raise BackendServiceException("User not authenticated.")

        query = select(User).where(User.id == token_data.user_id)
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            db_user = result.scalar_one_or_none()
            sess.expunge_all()

        if db_user:
            return db_user
        else:
            raise BackendServiceException("User not found.")

    async def logout(self, access_token: Optional[str], refresh_token: Optional[str]):
        if access_token:
            try:
                await self._blacklist_token(token=access_token)
            except:
                pass
        if refresh_token:
            try:
                await self._blacklist_token(token=refresh_token)
            except:
                pass

    @staticmethod
    async def _verify_password(plain_password: str, hashed_password: str) -> bool:
        correct_password: bool = bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        return correct_password

    @staticmethod
    def _get_password_hash(password: str) -> str:
        hashed_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        return hashed_password

    async def _authenticate_user(self, email: str, password: str) -> User | None:
        query = select(User).where(User.email == email)
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            db_user = result.scalar_one_or_none()
            sess.expunge_all()
        if not db_user:
            return None
        if not await self._verify_password(password, db_user.password):
            return None

        return db_user

    async def _create_token(self,
                            data: dict[str, Any],
                            token_type: TokenType
                            ) -> str:
        to_encode = data.copy()
        expire = datetime.now(UTC).replace(tzinfo=None) + settings.get_expiration(token_type=token_type)
        to_encode.update({"exp": expire, "token_type": token_type})
        encoded_jwt: str = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        await self._verify_token(token=encoded_jwt, expected_token_type=token_type)
        return encoded_jwt

    async def _verify_token(self, token: str, expected_token_type: TokenType) -> TokenData | None:
        query = select(TokenBlacklist).where(TokenBlacklist.token == token)
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            is_blacklisted = result.scalar_one_or_none()
        if is_blacklisted:
            return None
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: int = int(payload.get("sub"))
            token_type: str = payload.get("token_type")
            if user_id is None or token_type != expected_token_type:
                return None
            return TokenData(user_id=int(user_id))
        except PyJWTError as e:
            logger.exception(e)
            return None
        except Exception as e:
            logger.exception(e)
            return None

    async def _blacklist_token(self, token: str) -> None:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        expires_at = datetime.fromtimestamp(payload.get("exp"))
        async with self.db.session_scope() as sess:
            sess.add_all([
                TokenBlacklist(
                    token=token,
                    expires_at=expires_at
                )
            ])
