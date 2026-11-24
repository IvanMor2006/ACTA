from flask import Blueprint, render_template, redirect, url_for, request, flash
from itertools import groupby
import datetime

from .db import *
from .decorators import *

sp_pay_bp = Blueprint('sp_pay', __name__, url_prefix='')

@sp_pay_bp.route('sp/pay')
@role_required(['admin', 'admin_viewer'])
def sp():
    db = get_db()
    pays = db.execute("select * from v_pay_info pay order by to_date(cy_dr, 'dd.mm.yyyy') desc, pay, ol_naim, t_d desc, t_t desc").fetchall()
    pays_grouped = []
    for ku_dr, group in groupby(pays, key=lambda x: x['ku_dr']):
        pays_grouped.append({
            'list': list(group)
        })
    people_ol_pay = db.execute('''
      select ol.ku, ol.naim
      from sp_ol ol
      where ol.in_theater
        and ol.could_pay 
        and exists(
          select *
          from sp_dr dr
          where dr.ku_ol <> ol.ku
            and dr.ku not in (
              select pay.ku_dr 
              from sp_pay pay
              where pay.ku_ol = ol.ku
            )
        )
      order by ol.naim
    ''').fetchall()
    people_dr_pay = db.execute("""
      select dr.ku, dr.naim, dr.cy_dr
      from v_dr_info dr
      where exists (
        select *
        from sp_ol ol
        where dr.ku_ol <> ol.ku
          and ol.in_theater
          and ol.could_pay 
          and ol.ku not in (
            select pay.ku_ol
            from sp_pay pay
            where pay.ku_dr = dr.ku
          )
      )
      order by to_date(dr.cy_dr, 'dd.mm.yyyy') desc, dr.naim
    """).fetchall()
    return render_template('sp/pay/sp.html.j2', pays=pays_grouped, people_ol_pay=people_ol_pay, people_dr_pay=people_dr_pay)

@sp_pay_bp.route('/sp/pay/add', methods=['POST'])
@role_required(['admin'])
def add():
    ref = request.referrer
    try:
        ku_ol, ol_naim = request.form.get('a_pay_ol').split('|', 1)
        ku_dr, dr_naim = request.form.get('a_pay_dr').split('|', 1)
    except AttributeError as e:
        flash('Не указан человек или именник', 'danger')
        return redirect(ref)
    pay = request.form.get('a_pay_pay')

    try:
        db = get_db()
        db.execute('insert into sp_pay (ku_ol, ku_dr, pay) values (%s, %s, %s)',
                   (ku_ol, ku_dr, pay))
        db.commit()
        flash('Новый долг добавлен', 'success')
    except psycopg.errors.CheckViolation as e:
        if db: db.rollback()
        if 'sp_ol_balance_check' in str(e):
            flash('Недостаточно денег на балансе', 'danger')
    except psycopg.errors.UniqueViolation as e:
        if db: db.rollback()
        if 'uq_pay' in str(e):
            flash(f'Долг для {ol_naim} на день рождения {dr_naim} уже есть', 'danger')
    except psycopg.errors.RaiseException as e:
        if db: db.rollback()
        if 'sp_pay_ol_dr_not_self' in str(e):
            flash('Нельзя добавить долг для человека на его же день рождения', 'danger')
        elif 'sp_pay_pay_less_price' in str(e):
            flash('Нельзя добавить долг с оплатой, большей чем прайс', 'danger')
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        if db: db.close()
    return redirect(ref)

@sp_pay_bp.route('sp/pay/edit', methods=['POST'])
@role_required(['admin'])
def edit():
    ref = request.referrer
    ku = request.form.get('e_pay_ku')
    pay = request.form.get('e_pay_pay')

    try:
        db = get_db()
        db.execute('update sp_pay set pay = %s, dt = %s where ku = %s', (pay, datetime.datetime.now(), ku))
        db.commit()
    except psycopg.errors.CheckViolation as e:
        if db: db.rollback()
        if 'sp_ol_balance_check' in str(e):
            flash('Недостаточно денег на балансе', 'danger')
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        if db: db.close()
    return redirect(ref)

@sp_pay_bp.route('sp/pay/delete', methods=['POST'])
@role_required(['admin'])
def delete():
    ref = request.referrer
    ku = request.form.get('d_pay_ku')
    try:
        db = get_db()
        db.execute('delete from sp_pay where ku = %s', (ku,))
        db.commit()
        flash('Долг успешно удалён', 'success')
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        if db: db.close()
    return redirect(ref)