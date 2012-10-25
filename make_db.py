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
