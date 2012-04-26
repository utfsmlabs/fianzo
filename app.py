#!/usr/bin/env python2

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy

class default_config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///asdf.db'
    DEBUG = True

app = Flask(__name__)
app.config.from_object(default_config)
app.config.from_envvar('INVENTORY_SETTINGS', silent=True)

db = SQLAlchemy(app)

class AssetType(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    description = db.Column(db.String, unique=True)
    assets = db.relationship('Asset', backref='type')

    def __init__(self, description):
        self.description = description
    
    def __repr__(self):
        return '<Aset type %r>' % self.description

class Asset(db.Model):
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

@app.route('/')
def show_assets():
    types = AssetType.query.all()
    return render_template('show_assets.html', types = types)

if __name__ == '__main__':
    app.run()

