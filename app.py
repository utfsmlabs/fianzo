#!/usr/bin/env python2

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

class default_config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///asdf.db'
    DEBUG = True

app = Flask(__name__)
app.config.from_object(default_config)
app.config.from_envvar('INVENTORY_SETTINGS', silent=True)

db = SQLAlchemy(app)

# A word about users:
# In this particular implementation we have no table for users since they
# will be always be retrieved from LDAP. That's why all references to user, 
# in particular in lended_to fields shall be the dn of the user

class AssetType(db.Model):
    '''
    Category of the asset, such as "Laptop" or "iPad"
    '''
    id = db.Column(db.Integer, primary_key = True)
    description = db.Column(db.String, unique=True)
    assets = db.relationship('Asset', backref='type')

    def __init__(self, description):
        self.description = description
    
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
    description = db.Column(db.Text, default = '')

    def __init__(self, name, type):
        self.name = name
        self.type_id = type.id

    def __repr__(self):
        return '<Asset %r>' % self.name

class AssetLog(db.Model):
    '''
    Log used for accounting. Isn't actually checked by the application
    '''
    id = db.Column(db.Integer, primary_key = True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'))
    time = db.Column(db.DateTime(timezone=True))
    action = db.Column(db.Enum('checkin', 'checkout'))
    lended_to = db.Column(db.String)

    def __init__(self, asset, action, lended_to):
        self.time = datetime.now()
        self.asset_id = asset.id
        self.action = action
        self.lended_to = lended_to

@app.route('/')
def show_assets():
    types = AssetType.query.all()
    return render_template('show_assets.html', types = types)

if __name__ == '__main__':
    app.run()

