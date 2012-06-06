from wtforms import Form, TextField, PasswordField, IntegerField, SelectField, validators

class loginForm(Form):
    username = TextField('Username', [validators.required()])
    password = PasswordField('Password', [validators.required()])

class lendForm(Form):
    lended_to = TextField('Username', [validators.required()])

class AssetTypeForm(Form):
    name = TextField('Name', [validators.required()])
    loan_period_number = IntegerField('Lend time', [validators.NumberRange(min=0), validators.required()])
    loan_period_resolution = SelectField('Lend time resolution', [validators.required()], 
            choices=[('d', 'Days'), ('h', 'Hours'), ('m', 'Minutes')])

class AssetForm(Form):
    name = TextField('Name', [validators.required()])
