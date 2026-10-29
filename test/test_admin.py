from test.utils import *
from routers.admin import get_current_user,get_db


app.dependency_overrides[override_get_db] = get_current_user
app.dependency_overrides[get_db]  = override_get_db

def test_admin_read_all_authenticated():
    response=client.get('/admin/todo')
    assert response.status_code == status.HTTP_200_OK


def test_admin_create(test_todo):
    response=client.get('/admin/todo')
    assert response.status_code == status.HTTP_200_OK
    
    assert response.json() == [{'title':'Learn to code ','description':'Need to learn every day',
                                'priority':5,'complete':False,'id':1, 'owner_id':1}]


def test_admin_delete_todo(test_todo):
    response=client.delete('/admin/todo/1')
    assert response.status_code == status.HTTP_204_NO_CONTENT
    db=TestingSessionLocal()
    model=db.query(Todos).filter(Todos.id == 1).first()
    assert model is None

def test_admin_delete_todo_not_found(test_todo):
    
    response=client.delete('/admin/todo/9999')
    assert response.status_code == 404
    assert response.json()==  {'detail': 'not found !'}
    

