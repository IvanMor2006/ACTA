from functools import wraps
from flask import redirect, url_for, abort, request, flash

from .user_session import *

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session_get(USER_KU):
            flash('Нужно войти в аккаунт, чтобы открыть ссылку', 'warning')
            return redirect(url_for('auth.login', next_url=request.full_path.rstrip('?')))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session_get(USER_ROLE, 'guest') not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator