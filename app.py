#!/usr/bin/env python2

from flask import Flask, render_template, jsonify, request, flash, redirect, abort, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import ldapUsers

class default_config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///asdf.db'
    DEBUG = True
    LDAP_URI = 'ldap://localhost:3890'
    LDAP_SEARCH_ATTR = 'uid'
    LDAP_BASEDN = 'ou=inf,o=utfsm,c=cl'
    SECRET_KEY = 'development secret key'

app = Flask(__name__)
app.config.from_object(default_config)
app.config.from_envvar('INVENTORY_SETTINGS', silent=True)

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
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, unique=True)
    loan_period = db.Column(db.Interval)

    assets = db.relationship('Asset', backref='type')

    def __init__(self, name, loan_period = timedelta(minutes=90)):
        self.name = name
        self.loan_period = loan_period
    
    def __repr__(self):
        return '<Aset type %r>' % self.description


class Asset(db.Model):
    '''
    Particular, singular asset, identified by serial number
    '''
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    type_id = db.Column(db.Integer, db.ForeignKey('asset_type.id'))
    lended_to = db.Column(db.String)
    loan_ends_at = db.Column(db.DateTime(timezone=True))

    logs = db.relationship('AssetLog', backref='asset')

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
    id = db.Column(db.Integer, primary_key = True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'))
    time = db.Column(db.DateTime(timezone=True))
    action = db.Column(db.Enum('lend', 'return'))
    lended_to = db.Column(db.String)
    return_status = db.Column(db.Enum('regular', 'late'))

    def __init__(self, lended_to, action, asset=None, asset_id=None):
        self.time = datetime.now()
        if asset:
            self.asset_id = asset.id
        else:
            self.asset_id = asset_id

        self.action = action
        self.lended_to = lended_to

    def lended_to_name(self):
        return ldapUsers.extractNamingAttribute(self.lended_to)


@app.route('/')
def show_assets():
    types = AssetType.query.all()
    overdue_assets = Asset.query.filter(Asset.loan_ends_at < datetime.now())
    return render_template('show_assets.html', types = types, overdue_assets = overdue_assets)


@app.route('/asset/<int:asset_id>/lend', methods=['POST', 'GET'])
def lend_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)

    if asset.lended_to:
        print asset.lended_to
        flash('%s is already lent' % asset.name)
        return redirect(url_for('show_assets'))

    if request.method == 'GET':
        return render_template('lend_asset.html', asset_id=asset_id)
    elif request.method == 'POST':
        dn = ldap.getDN(request.form['lended_to'])
        if not dn:
            return render_template('lend_asset.html',
                    asset_id=asset_id,
                    error='%s not found' % request.form['lended_to'])
        
        asset.lended_to = dn
        asset.loan_ends_at = datetime.now() + asset.type.loan_period
        log = AssetLog(dn, 'lend', asset)
        db.session.add(asset)
        db.session.add(log)
        db.session.commit()

        flash('Lended %s to %s' % (asset.name, asset.lended_to_name()))

        return redirect(url_for('show_assets'))


@app.route('/asset/(<int:asset_id>/return')
def return_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    log = AssetLog(asset.lended_to, 'return', asset)

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


@app.route('/log/<int:page>')
def show_log(page):
    pagination = AssetLog.query.order_by(
            db.desc(AssetLog.time)).paginate(page, 30)
    return render_template('show_log.html', pagination=pagination)


@app.route('/log/')
def redirect_to_show_log():
    return redirect(url_for('show_log', page=1))


if __name__ == '__main__':
    app.run(host='0.0.0.0')

