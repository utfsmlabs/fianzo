from wtforms import Form, TextField, PasswordField, validators

class loginForm(Form):
    username = TextField('Username', [validators.required()])
    password = PasswordField('Password', [validators.required()])