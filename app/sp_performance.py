from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from itertools import groupby

from .db import *
from .decorators import *
from .user_session import *
from .s3 import *

sp_performance_bp = Blueprint('sp_performance', __name__, url_prefix='')

@sp_performance_bp.route('/sp/performance')
def sp():
    db = get_db()
    plays = db.execute('select * from v_performance_info order by status, premiere_date desc, naim').fetchall()
    plays_grouped = []
    for status, group in groupby(plays, key=lambda x: x['status']):
        plays_grouped.append({
            'list': list(group)
        })
    play_statuses = db.execute('select * from v_performance_status').fetchall()
    db.close()
    return render_template('sp/performance/sp.html.j2', plays=plays_grouped, play_statuses=play_statuses)

@sp_performance_bp.route('/sp/performance/add', methods=['POST'])
@role_required(['admin'])
def add():
    ref = request.referrer

    naim = request.form.get('a_performance_naim')
    status = request.form.get('a_performance_status')
    premiere_date = request.form.get('a_performance_premiere_date') or None

    file = request.files.get('a_performance_poster')
    poster_url = None

    try:
        db = get_db()
        ku = db.execute('insert into sp_performance (naim, status, premiere_date) values (%s, %s, %s) returning ku', (naim, status, premiere_date)).fetchone()['ku']

        if file and file.filename != '':
            poster_url = process_and_upload_image(file, f'sp_performance_{ku}')
            if poster_url:
                db.execute('update sp_performance set poster_url = %s where ku = %s', (poster_url, ku))
            else:
                flash('Спектакль добавлен, но картинку загрузить не удалось', 'warning')
        db.commit()
        flash('Новый спектакль добавлен', 'success')
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        if db: db.close()
    return redirect(ref)