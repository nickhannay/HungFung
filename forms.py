from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, BooleanField, TextField, TextAreaField, SelectField, DecimalField,DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms.fields.html5 import DateField


#Form for inserting new employee
class NewEmployeeForm(FlaskForm):
    employee_first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=100)]) 
    employee_middle_name = StringField('Middle Name',validators=[ Length(max=100)]) 
    employee_last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=100)])
    employee_SIN = StringField('Social Insurance Number (SIN)', validators=[DataRequired(), Length(min=9, max=9)])
    employee_phone = StringField('Phone Number', validators=[DataRequired(), Length(min=1, max=20)])
    employee_Address= StringField('Home Address', validators=[Length(min=0, max=100)])
    employee_date_of_birth = StringField('Date of Birth', validators=[DataRequired(), Length(min=1, max=25)])
    roles=["Office", "Operation"]
    employee_role = SelectField('Department', choices = roles, validators = [DataRequired()])
    employee_salary = DecimalField('Salary/Wage', places=2, validators=[DataRequired()])
    submit = SubmitField('Add New Employee')

class UpdateEmployeeFilloutFrom(FlaskForm):
    # new values entered in here
    employee_first_name = StringField('First Name', validators= [Length( max=100)]) 
    employee_middle_name = StringField('Middle Name',validators= [Length(max=100)]) 
    employee_last_name = StringField('Last Name', validators= [Length( max=100)])
    employee_SIN = StringField('Social Insurance Number (SIN)', validators= [Length( max=9)])
    employee_phone = StringField('Phone Number', validators= [Length(max=20)])
    employee_Address= StringField('Home Address', validators= [Length( max=100)])
    employee_date_of_birth = StringField('Date of Birth', validators= [Length( max=25)])

    employee_role = SelectField('Department')
    employee_salary = StringField('Salary/Wage')

    submit = SubmitField('Save Changes')



class PayrollForm(FlaskForm):
    employee_filter = SelectField('Employee', coerce=str)
    options = ["Last 25", "YTD"]
    payroll_date_range = SelectField('Filter Stubs By', choices = options, validators = [DataRequired()])
    submit = SubmitField('Get Pay Stubs')

class GeneratePayStub(FlaskForm):
    employee_filter_pay_stub = SelectField('Employee', coerce=str)
    start_date = DateField('Start Date',format='%Y-%m-%d', validators = [DataRequired()])
    end_date = DateField('End Date',format='%Y-%m-%d', validators = [DataRequired()])
    generate_pay_stub = SubmitField('Generate Pay Stub')

class Add_shift_form(FlaskForm):
    employee_filter = SelectField('Employee', validators = [DataRequired()])
    date_of_shift = DateField('Date of Shift',format='%Y-%m-%d', validators = [DataRequired()])
    options=[]
    for i in range(1,25):
        options.append(i)
    shift_start_time = SelectField('Start Time', choices = options, validators = [DataRequired()])
    sift_end_time = SelectField('End Time', choices = options, validators = [DataRequired()])
    submit = SubmitField('Add Shift')

class get_shifts_form(FlaskForm):
    employee_filter = SelectField('Employee', coerce=str)
    submit = SubmitField('Get Timecards')

class RemoveContactForm(FlaskForm):
    submit = SubmitField('Delete')

class RemoveEmployeeForm(FlaskForm):
    submit = SubmitField('Delete')

class ContactForm(FlaskForm):
    emergency_contact_employee = SelectField('Employee', coerce=str)
    emergency_contact_name = StringField('Contact Full Name', validators=[DataRequired(), Length(min=1, max=100)])
    emergency_contact_phone = StringField('Contact Phone Number', validators=[DataRequired(), Length(min=10, max=10)])
    emergency_contact_relation = StringField('Relationship with Employee', validators=[DataRequired(), Length(min=1, max=25)]) 
    submit = SubmitField('Add Contact')

class update_employee_info_form(FlaskForm):
    employee_update  = SelectField('Select the employee you would like to update', coerce=str)
    submit = SubmitField('Update')


