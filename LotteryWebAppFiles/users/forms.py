import re
import pyotp
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import Required, Email, Length, EqualTo, ValidationError

# List of characters which cannot be included in password
def character_check(form, field):
    excluded_chars = " * ? ! ' ^ + % & / ( ) = } ] [ { $ # @ < >"

    # If excluded character found in any field with 'character check' parameter, return error message
    for char in field.data:
        if char in excluded_chars:
            raise ValidationError(
                f"Character {char} is not allowed.")

# Usser registration form
class RegisterForm(FlaskForm):
    email = StringField(validators=[Required(), Email()])
    firstname = StringField(validators=[Required(), character_check])
    lastname = StringField(validators=[Required(), character_check])
    phone = StringField(validators=[Required()])
    password = PasswordField(validators=[Required(), Length(min=6, max=12,
                                                            message='Password must be between 6 and 12 characters in length.')])
    confirm_password = PasswordField(validators=[Required(), EqualTo('password',
                                                                     message='Passwords must be equal to one another.')])
    pin_key = StringField(validators=[Required(), character_check, Length(min=32, max=32,
                                                         message='PIN key must be exactly 32 characters in length.')])
    submit = SubmitField()

    # Ensures that password meets requirements
    def validate_password(self, password):
        p = re.compile(r'(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[\W])')
        if not p.match(self.password.data):
            raise ValidationError("Password must contain at least 1 digit, 1"
                                  " uppercase letter, 1 lowercase letter and 1"
                                  " special character.")

    # Checks format of phone number to meet requirements
    def validate_phone(self, phone):
        p = re.compile(r'(^\d{4}-\d{3}-\d{4}$)')
        if not p.match(self.phone.data):
            raise ValidationError("Phone number must be of the form"
                                  " XXXX-XXX-XXXX")

# LOGIN form
class LoginForm(FlaskForm):
    username = StringField(validators=[Required(), Email()])
    password = PasswordField(validators=[Required()])
    pin = StringField(validators=[Required(), Length(min=6, max=6, message=
                                                     'OTP must be 6 characters in length')])
    submit = SubmitField()
