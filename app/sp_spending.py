from flask import Blueprint, render_template, redirect, url_for, request, flash
from .db import *
from .decorators import *

sp_spending_bp = Blueprint('sp_spending', __name__, url_prefix='')

@sp_spending_bp.route('/sp/dr/<int:ku_dr>/spending/add', methods=['POST'])
@role_required(['admin'])
def add(ku_dr):
    naim = request.form.get('a_spending_naim')
    cost = request.form.get('a_spending_cost')

    try:
        db = get_db()
        db.execute('insert into sp_spending (naim, cost, ku_dr) values (%s, %s, %s)',
                   (naim, cost, ku_dr))
        db.commit()
        flash('Новая покупка добавлена', 'success')
    except psycopg.errors.CheckViolation as e:
        if db: db.rollback()
        flash(f'Стоимость должна быть не меньше нуля', 'danger')
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        if db: db.close()
    return redirect(url_for('sp_dr.dr', ku=ku_dr))