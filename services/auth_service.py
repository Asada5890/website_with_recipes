from datetime import datetime, timedelta
import jwt
from core.settings import settings
from schemas.auth import AuthSub, Token
from schemas.user import UserDTO


class UserNotFound(Exception):
    """
    Своя ошибка, если пользователь не был найден
    """
    pass


class AuthService:
    """
    Класс для аутентификации пользователей и работы с токенами доступа.
    """

    def create_access_token(self, data: AuthSub, ) -> str:
        """
        Создает JWT токен доступа.

        :param data: Данные, которые будут закодированы в токене (например, email пользователя).
        :param expires_delta: Время жизни токена (timedelta).
        :return: Закодированный JWT токен в виде строки.
        """
        data_to_encode = data.dict()
        data_to_encode.update({'exp': datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)})
        return jwt.encode(
            data_to_encode,
            settings.SECRET_KEY,  # JH9pfiY86p
            headers={'alg': settings.JWT_ALGORITHM, 'typ': 'JWT'}
        )

    def create_refresh_token(self, data: AuthSub):
        data_to_encode = data.dict()
        data_to_encode.update({'exp': datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)})
        return jwt.encode(
            data_to_encode,
            settings.SECRET_KEY,
            headers={'alg': settings.JWT_ALGORITHM, 'typ': 'JWT'}
        )




    def login(self, user:UserDTO ) -> Token:
        """
        Проверяет учетные данные пользователя и создает токен доступа.

        :param email: Электронная почта пользователя.
        :param password: Пароль пользователя.
        :return: Объект Token с токеном доступа и его типом.
        :raises HTTPException: Если учетные данные неверны.
        """
        access_token = self.create_access_token(AuthSub(**user.model_dump()))  
        refresh_token = self.create_refresh_token(AuthSub(**user.model_dump()))  

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def register(self, user: UserDTO) -> Token:
        access_token = self.create_access_token(AuthSub(**user.model_dump())) 
        refresh_token = self.create_refresh_token(AuthSub(**user.model_dump()))

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
