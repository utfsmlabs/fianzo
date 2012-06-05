#!/usr/bin/env python2

from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, jsonify, request, flash, redirect,\
        abort, url_for, session
from flask.ext.sqlalchemy import SQLAlchemy

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
    IGNORE_AUTH = True

app = Flask(__name__)
app.config.from_object(default_config)
app.config.from_envvar('FIANZO_SETTINGS', silent=True)

db = SQLAlchemy(app)

ldap = ldapUsers.ldapConnection(app)

# A word about users:
# In this particular implementation we have no table for users since they
# will be always be retrieved from LDAP. That's why all references to user, 
# in particular in lended_to fields shall be the dn of the user

class AssetType(db.Model):
    '''
    Category of the asset, such as "Laptop" or "iPad"
    '''
    id = db.Column(db.Integer, primary_key = True, nullable=False)
    name = db.Column(db.String, unique=True, nullable=False)
    loan_period = db.Column(db.Interval, nullable=False)

    assets = db.relationship('Asset', backref='type', cascade='all, delete, delete-orphan')

    def __init__(self, name, loan_period = timedelta(minutes=90)):
        self.name = name
        self.loan_period = loan_period
    
    def __repr__(self):
        return '<Aset type %r>' % self.description


class Asset(db.Model):
    '''
    Particular, singular asset, identified by serial number
    '''
    id = db.Column(db.Integer, primary_key = True, nullable=False)
    name = db.Column(db.String, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('asset_type.id'), nullable=False)
    lended_to = db.Column(db.String)
    loan_ends_at = db.Column(db.DateTime(timezone=True))

    logs = db.relationship('AssetLog', backref='asset', cascade='all, delete, delete-orphan')

    def __init__(self, name, type=None, type_id=None):
        self.name = name
        if type:
            self.type_id = type.id
        else:
            self.type_id=type_id

    def __repr__(self):
        return '<Asset %r>' % self.name

    def lended_to_name(self):
        return ldapUsers.extractNamingAttribute(self.lended_to)

    def available(self):
        if self.lended_to == '' or self.lended_to is None:
            return True
        else:
            return False

    def overdue(self):
        if self.loan_ends_at and self.loan_ends_at < datetime.now():
            return True
        else:
            return False


class AssetLog(db.Model):
    '''
    Log used for accounting. Isn't actually checked by the application
    '''
    id = db.Column(db.Integer, primary_key = True, nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False)
    action = db.Column(db.Enum('lend', 'return'), nullable=False)
    lended_to = db.Column(db.String, nullable=False)
    return_status = db.Column(db.Enum('regular', 'late'), nullable=False)
    action_by = db.Column(db.String, nullable=False)

    def __init__(self, lended_to, action, action_by, asset=None, asset_id=None):
        self.time = datetime.now()
        if asset:
            self.asset_id = asset.id
        else:
            self.asset_id = asset_id

        self.action = action
        self.lended_to = lended_to
        self.action_by = action_by

    def lended_to_name(self):
        return ldapUsers.extractNamingAttribute(self.lended_to)


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
    overdue_assets = Asset.query.filter(Asset.loan_ends_at < datetime.now())
    return render_template(
            'show_assets.html', types = types, overdue_assets = overdue_assets)


@app.route('/asset/<int:asset_id>/lend', methods=['POST', 'GET'])
@requires_auth
def lend_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)

    if asset.lended_to:
        flash('%s is already lent' % asset.name)
        return redirect(url_for('show_assets'))

    form = forms.lendForm(request.form)
    if request.method == 'POST'and form.validate():
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

    print form.lended_to.errors
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
        db.session.add(type)
        db.session.commit()
        return redirect(url_for('show_assets_for_edit'))
    else:
        return  render_template('asset_type_form.html', form=form, action_url=url_for('new_asset_type'))


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
        db.session.add(type)
        db.session.commit()
        flash('Asset type edited succesfully')
        return redirect(url_for('show_assets_for_edit'))
    return render_template('asset_type_form.html', form = form, action_url = url_for(
        'edit_asset_type', asset_type_id=asset_type_id))


@app.route('/log/<int:page>')
@requires_auth
def show_log(page):
    pagination = AssetLog.query.order_by(
            db.desc(AssetLog.time)).paginate(page, 15)
    return render_template('show_log.html', pagination=pagination)


@app.route('/log/')
def redirect_to_show_log():
    return redirect(url_for('show_log', page=1))


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


if __name__ == '__main__':
    app.run(host='0.0.0.0')

