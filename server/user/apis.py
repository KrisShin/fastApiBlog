from datetime import timedelta

from fastapi import APIRouter, status, HTTPException, Request

from common.global_variable import PMResponse
from common.utils import set_cache
from config.settings import ACCESS_TOKEN_EXPIRE_DAYS
from user.models import User
from user.pydantics import UserLoginPydantic, UserInfoPydantic
from user.utils import get_password_hash, verify_password, create_access_token

router = APIRouter()


@router.post('/register/', response_model=PMResponse)
async def post_register_user(user: UserLoginPydantic):
    password_hash = get_password_hash(user.password)
    user_obj = await User.get_or_none(username=user.username)
    if not user_obj:
        user_obj = await User.create(username=user.username, password=password_hash)
        response_data = UserInfoPydantic.from_orm(user_obj)
        return {'code': status.HTTP_200_OK, 'data': response_data}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='username exist.')


@router.post('/token/')
async def post_user_token(user: UserLoginPydantic, request: Request):
    user_obj = await User.get_or_none(username=user.username)
    if not user_obj or (user and user_obj.disabled):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='username exist.')
    if not verify_password(user.password, user_obj.password):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Wrong password.')
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    token = create_access_token(user_id=user_obj.id, expires_delta=access_token_expires)
    await set_cache(request, token, str(user_obj.id), access_token_expires)
    return {'token': token}