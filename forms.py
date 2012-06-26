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

