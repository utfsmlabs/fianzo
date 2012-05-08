#!/usr/bin/env python2

from app import db, AssetType, Asset
db.create_all()

t = AssetType('Laptop')
db.session.add(t)
db.session.commit()

for i in range(1, 10):
    a = Asset('Laptop %d' % i, type = t)
    db.session.add(a)

db.session.commit()
