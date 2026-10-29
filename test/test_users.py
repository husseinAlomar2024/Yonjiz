from test.utils import *
from routers.users import get_current_user,get_db

app.dependency_overrides[get_db]=override_get_db
app.dependency_overrides[get_current_user]=override_get_current_user

def test_return_user(test_users):
    response=client.get('/users')

    assert response.status_code==200
    assert response.json()['username'] == 'hussein'
    assert response.json()['email'] == 'potato_patata'
    assert response.json()['first_name'] == 'hussein'
    assert response.json()['last_name'] == 'mousa'
    assert response.json()['role'] == 'admin'
    assert response.json()['phone_number'] == '0787094322'




def test_change_password_success(test_users):
     response = client.put("/users/password", json={"password": "1234", "new_password": "newpassword"})
                                                                              
     assert response.status_code == status.HTTP_204_NO_CONTENT 



def test_change_password_invalid_current_password(test_users):
     
            response = client.put("/users/password", json={"password": "134",
                 "new_password": "newpassword"})
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json() == {'detail': 'incorrect password'}

def test_change_phone_number_success(test_users):
         response = client.put("/users/update_phone_number",json="2222222222")
         assert response.status_code == status.HTTP_204_NO_CONTENT
