from foreignlanguage.models import User, Student


def get_user_by_id(uid):
    return Student.query.get(uid)