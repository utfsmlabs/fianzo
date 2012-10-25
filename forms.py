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

from wtforms import Form, TextField, PasswordField, IntegerField, SelectField, validators

class loginForm(Form):
    username = TextField('Username', [validators.required()])
    password = PasswordField('Password', [validators.required()])

class lendForm(Form):
    lended_to = TextField('Username', [validators.required()])

class AssetTypeForm(Form):
    name = TextField('Name', [validators.required()])
    loan_period_days = IntegerField('Loan days', 
            [validators.NumberRange(min=0)], default=0)
    loan_period_hours = IntegerField('Loan hours', 
            [validators.NumberRange(min=0)], default=1)
    loan_period_minutes = IntegerField('Loan minutes', 
            [validators.NumberRange(min=0)], default=30)

class AssetForm(Form):
    name = TextField('Name', [validators.required()])

