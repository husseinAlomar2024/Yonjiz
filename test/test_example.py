import pytest


def test_equal_or_not_equal():
    assert 2==2


def test_inst():
    assert isinstance("Is this string ?",str)
    assert not isinstance("234",int)

def test_type():
    assert type("world" is not int)

def test_list():
    mylist=[1,23,4,5,6]
    assert 7  not in mylist  


class Student:
     def __init__(self,first_name:str,last_name:str,major:str,years:int):
         self.first_name=first_name
         self.last_name=last_name
         self.major=major
         self.years=years

@pytest.fixture
def default_employee():
    return Student("john","doe","cs",4)


def test_porson_initialization(default_employee):
   
    assert default_employee.first_name=="john","first name is john"
    assert default_employee.last_name=="doe","it should be me "
    assert default_employee.major=="cs","dddddih"
    assert default_employee.years==4