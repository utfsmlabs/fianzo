#!/usr/bin/env python

# Copyright (C) 2012 Universidad Tecnica Federico Santa Maria
#
# This file is part of Fianzo.
#
# Fianzo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fianzo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fianzo.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, render_template, jsonify, request, flash, redirect,
        abort, url_for, session)

from models import db, Asset, AssetType, AssetLog, Ban
import ldapUsers
import forms

class default_config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///asdf.db'
    DEBUG = True
    LDAP_URI = 'ldap://localhost:3890'
    LDAP_SEARCH_ATTR = 'uid'
    LDAP_BASEDN = 'ou=inf,o=utfsm,c=cl'
    SECRET_KEY = 'development secret key'
    ADMINS = set(['javier.aravena'])
    IGNORE_AUTH = False
    LOG_FILE = 'fianzo.log'

app = Flask(__name__)
app.config.from_object(default_config)
app.config.from_envvar('FIANZO_SETTINGS', silent=True)
app.config.from_pyfile('config.py', silent=True)

ldap = ldapUsers.ldapConnection(app)
db.init_app(app)

def requires_auth(f):
    '''
    Decorator that checks wether the user is logged in and redirects
    to the login form if he isn't
    '''
    @wraps(f)
    def decorated(*args, **kwargs):
        if app.config['IGNORE_AUTH'] or 'username' in session:
            return f(*args, **kwargs)
        else:
            flash('This page requires login')
            return redirect(url_for('login'))
    return decorated

@app.context_processor
def user_processor():
    '''
    Makes the user name available to the templates
    '''
    u = None
    if 'username' in session:
        u = session['username']
    return dict(username=u)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.loginForm(request.form)
    if request.method == 'POST' and form.validate():
        if form.username.data in app.config['ADMINS'] and ldap.search_and_auth(
                form.username.data, form.password.data):
            session['username'] = form.username.data
            return redirect(url_for('show_assets'))
        else:
            flash('incorrect username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('show_assets'))


@app.route('/')
@requires_auth
def show_assets():
    types = AssetType.query.all()
    overdue_assets = Asset.query.filter(
            Asset.loan_ends_at < datetime.now()).order_by(Asset.name)
    unavailable_assets = Asset.query.filter(
            Asset.lended_to != None, Asset.lended_to != '')
    return render_template('show_assets.html', 
            types = types, overdue_assets = overdue_assets, unavailable_assets = unavailable_assets)


@app.route('/asset/<int:asset_id>/lend', methods=['POST', 'GET'])
@requires_auth
def lend_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)

    if asset.lended_to:
        flash('%s is already lent' % asset.name)
        return redirect(url_for('show_assets'))

    form = forms.lendForm(request.form)
    if request.method == 'POST' and form.validate():
        dn = ldap.getDN(form.lended_to.data)
        if dn:
            asset.lended_to = dn
            asset.loan_ends_at = datetime.now() + asset.type.loan_period
            log = AssetLog(dn, 'lend', session['username'], asset=asset)
            db.session.add(asset)
            db.session.add(log)
            db.session.commit()
            flash('Lended %s to %s' % (asset.name, asset.lended_to_name()))
            return redirect(url_for('show_assets'))
        else:
            form.lended_to.errors.append(
                    'User %s not found' % form.lended_to.data)

    return render_template('lend_asset.html', asset_id=asset_id, form=form)


@app.route('/asset/<int:asset_id>/return')
@requires_auth
def return_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    log = AssetLog(asset.lended_to, 'return', session['username'], asset=asset)

    if asset.overdue() is True:
        log.return_status = 'late'
    else:
        log.return_status = 'regular'

    asset.lended_to = None
    asset.loan_ends_at = None
    db.session.add(log)
    db.session.add(asset)
    db.session.commit()

    flash('Returned %s' % asset.name)
    return redirect(url_for('show_assets'))


@app.route('/edit')
@requires_auth
def show_assets_for_edit():
    types = AssetType.query.all()
    return render_template('show_assets_for_edit.html', types = types)


@app.route('/asset_type/new', methods=['POST', 'GET'])
@requires_auth
def new_asset_type():
    form = forms.AssetTypeForm(request.form)

    if request.method == 'POST' and form.validate():
        type = AssetType(form.name.data)
        period = timedelta(days = form.loan_period_days.data,
                hours = form.loan_period_hours.data,
                minutes = form.loan_period_minutes.data)
        type.loan_period = period
        db.session.add(type)
        db.session.commit()
        return redirect(url_for('show_assets_for_edit'))
    else:
        return  render_template('asset_type_form.html',
                form=form, action_url=url_for('new_asset_type'))


@app.route('/asset_type/<int:asset_type_id>/delete')
@requires_auth
def ask_delete_asset_type(asset_type_id):
    type = AssetType.query.get_or_404(asset_type_id)
    return  render_template('confirm.html',
            title = 'Remove asset type',
            message = 'Do you want to remove %s' % type.name,
            actions = [
                ('Cancel', url_for('show_assets_for_edit')),
                ('Delete', url_for('delete_asset_type', asset_type_id=asset_type_id))
                ]
            )

@app.route('/asset_type/<int:asset_type_id>/delete/confirm')
@requires_auth
def delete_asset_type(asset_type_id):
    type = AssetType.query.get_or_404(asset_type_id)
    name = type.name
    db.session.delete(type)
    db.session.commit()
    flash('Deleted type %s' % name)
    return redirect(url_for('show_assets_for_edit'))


@app.route('/asset_type/<int:asset_type_id>', methods=['POST', 'GET'])
@requires_auth
def edit_asset_type(asset_type_id):
    type = AssetType.query.get_or_404(asset_type_id)

    form = forms.AssetTypeForm(request.form, type)

    if request.method == 'POST' and form.validate():
        type.name = form.name.data
        period = timedelta(days = form.loan_period_days.data,
                hours = form.loan_period_hours.data,
                minutes = form.loan_period_minutes.data)
        type.loan_period = period

        db.session.add(type)
        db.session.commit()
        flash('Asset type edited succesfully')
        return redirect(url_for('show_assets_for_edit'))
    else:
        form.loan_period_days.data = type.loan_period.days
        form.loan_period_hours.data = type.loan_period.seconds / 3600
        form.loan_period_minutes.data = (type.loan_period.seconds % 3600) / 60
        return render_template('asset_type_form.html', form = form,
                action_url = url_for( 'edit_asset_type', asset_type_id=asset_type_id))


@app.route('/log/<int:page>')
@requires_auth
def show_log(page):
    pagination = AssetLog.query.order_by(
            db.desc(AssetLog.time)).paginate(page, 15)
    return render_template('show_log.html', pagination=pagination)


@app.route('/log/')
def redirect_to_show_log():
    return redirect(url_for('show_log', page=1))


@app.route('/asset_type/<int:type_id>/new_asset', methods=['GET', 'POST'])
@requires_auth
def new_asset(type_id):
    type = AssetType.query.get_or_404(type_id)
    form = forms.AssetForm(request.form)
    if request.method == 'POST' and form.validate():
        asset = Asset(form.name.data, type = type)
        db.session.add(asset)
        db.session.commit()
        return redirect(url_for('show_assets_for_edit'))
    else:
        return render_template('asset_form.html', form = form)


@app.route('/asset/<int:asset_id>', methods=['GET', 'POST'])
@requires_auth
def edit_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    form = forms.AssetForm(request.form, asset)
    if request.method == 'POST' and form.validate():
        asset.name = form.name.data
        db.session.add(asset)
        db.session.commit()
        return redirect(url_for('show_assets_for_edit'))
    else:
        return render_template('asset_form.html', form = form)

@app.route('/asset/<int:asset_id>/delete')
@requires_auth
def ask_delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    return  render_template('confirm.html',
            title = 'Remove asset',
            message = 'Do you want to remove %s' % asset.name,
            actions = [
                ('Cancel', url_for('show_assets_for_edit')),
                ('Delete', url_for('delete_asset', asset_id=asset_id))
                ]
            )

@app.route('/asset/<int:asset_id>/delete/confirm')
@requires_auth
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    name = asset.name
    db.session.delete(asset)
    db.session.commit()
    flash('Deleted type %s' % name)
    return redirect(url_for('show_assets_for_edit'))

def config_string():
    s = ['%s = %s\n' % (k, v) for k, v in app.config.iteritems()]
    return ''.join(s)

if __name__ == '__main__':
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(app.config['LOG_FILE'],
                maxBytes = 1024 * 250, backupCount = 2)
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)
    app.logger.debug(config_string())
    app.run(host='0.0.0.0')

