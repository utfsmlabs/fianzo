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

# A word about users:
# In this particular implementation we have no table for users since they
# will be always be retrieved from LDAP. That's why all references to user, 
# in particular in lended_to fields shall be the dn of the user

from datetime import datetime, timedelta
from flask.ext.sqlalchemy import SQLAlchemy
import ldapUsers

db = SQLAlchemy()

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
        return '<Aset type %r>' % self.name


class Asset(db.Model):
    '''
    Particular, singular asset, identified by serial number
    '''
    id = db.Column(db.Integer, primary_key = True, nullable=False)
    name = db.Column(db.String, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('asset_type.id'), nullable=False)
    lended_to = db.Column(db.String) #if this is None/NULL then it's available
    loan_ends_at = db.Column(db.DateTime())

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
    time = db.Column(db.DateTime(), nullable=False)
    action = db.Column(db.Enum('lend', 'return', name='action_enum'), nullable=False)
    lended_to = db.Column(db.String, nullable=False)
    return_status = db.Column(db.Enum('regular', 'late', name='status_enum'))
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


class Ban(db.Model):
    '''
    Indicates the banning of a user
    '''
    id = db.Column(db.Integer, primary_key = True, nullable=False)
    user = db.Column(db.String, nullable = False)
    banned_until = db.Column(db.DateTime)
    times_banned = db.Column(db.Integer, nullable=False)

    def __init__(self, user, banned_until=None, times_banned=0):
        self.user = user
        self.banned_until = banned_until
        self.times_banned = times_banned

