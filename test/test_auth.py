from test.utils import *

from routers.auth import get_current_user,get_db,authnticate,create_access_token,SECRET_KEY,ALGORITHM
from jose import jwt
from datetime import timedelta
app.dependency_overrides[get_db]=override_get_db
import pytest
from fastapi import HTTPException

def test_authnticate_user(test_users):
    db=TestingSessionLocal()
    authnticated_user=authnticate(test_users.username,'1234',db)
    assert authnticated_user is not None
    assert authnticated_user.username==test_users.username

    non_existent_user=authnticate('39993jd','1234',db)
    assert non_existent_user is False

    wrong_password_user=authnticate(test_users.username,'333234',db)
    assert wrong_password_user is False
     



def test_create_access_token():
     username = 'testuser'
     user_id = 1

     role = 'user'
     expires_delta = timedelta(days=1)

     token = create_access_token(username, user_id, role, expires_delta)
     decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],options={'verify_signature': False})


     assert decoded_token['sub'] == username
     assert decoded_token['id'] == user_id
     assert decoded_token['role'] == role



@pytest.mark.asyncio
async def test_get_current_user_valid_token():
     encode={'sub':'testuser','id':1,'role':'admin'}
     token=jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)
     user = await get_current_user(token=token)
     assert user== {'username':'testuser','id':1,'user_role':'admin'}


@pytest.mark.asyncio
async def test_get_current_user_missing_payload():
     encode = {'role' : 'user'}
     token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

     with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=token)

     assert excinfo.value.status_code == 401
     assert excinfo.value.detail == 'Could not validate the user'