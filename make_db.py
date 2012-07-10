#!/usr/bin/env python
from app import db, AssetType, Asset, app
from pprint import PrettyPrinter

pp = PrettyPrinter(indent=4)
pp.pprint(app.config)

db.drop_all()
db.create_all()

t = AssetType('Laptop')
db.session.add(t)
db.session.commit()

for i in range(1, 10):
    a = Asset('Laptop %d' % i, type = t)
    db.session.add(a)

db.session.commit()
