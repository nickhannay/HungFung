import os
import sqlite3
from datetime import datetime, date
import sys
import secrets


from flask import Flask, render_template, url_for, flash, redirect, request
from forms import NewEmployeeForm, update_employee_info_form, RemoveEmployeeForm, UpdateEmployeeFilloutFrom ,PayrollForm, ContactForm, RemoveContactForm, Add_shift_form, get_shifts_form, GeneratePayStub
from wtforms.fields import Label 

from decimal import *

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from shifts import shift_pages
from employees import employee_pages
from payroll import payroll_pages
from shared_functions import *


def create_app(test_config=None):
        
        # create and configure the app
        app = Flask(__name__, instance_relative_config=True)
        app.config.from_mapping(
                SECRET_KEY = secrets.token_urlsafe(16),
                DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        )

        if test_config is None:
                # load the instance config, if it exists, when not testing
                app.config.from_pyfile('config.py', silent=True)
        else:
                # load the test config if passed in
                app.config.from_mapping(test_config)

        # ensure the instance folder exists
        try:
                os.makedirs(app.instance_path)
        except OSError:
                pass
        
        
        app.register_blueprint(shift_pages)    # shifts.py
        app.register_blueprint(employee_pages) # employees.py
        app.register_blueprint(payroll_pages)  # payroll.py
     
        
        @app.route('/')
        def index():
                
                print (sys.path)
                return render_template('index.html')



        @app.route('/emergency', methods=['GET', 'POST'])
        def emergency():
                connection = sqlite3.connect("instance/flaskr.sqlite")
                connection.row_factory = dict_factory
                cur = connection.cursor()
                cur.execute("PRAGMA foreign_keys=on")
                # get emergency contact info
                cur.execute('''
                                SELECT EC.ContactName, EC.PhoneNumber, 
                                EC.Relation, E.Fname, E.Lname
                                FROM EmergencyContact EC, Employee E 
                                WHERE EC.ID = E.EmployeeID 
                                ORDER BY E.Lname, E.Fname ASC
                         ''')
                emergency_contacts = cur.fetchall()

                connection.commit()
                cur.close()
                return render_template('emergency.html',  emergency_contacts = emergency_contacts)
        
        @app.route('/add_emergency_contact', methods=['GET', 'POST'])
        def add_emergency_contact():
                form =  ContactForm()

                # open database connection
                conn = sqlite3.connect("instance/flaskr.sqlite")
                conn.row_factory = dict_factory
                cur = conn.cursor()
                cur.execute("PRAGMA foreign_keys=on")
                # Populate drop down dynamically
                cur.execute(''' SELECT EmployeeID, Fname, Lname FROM Employee''')
                employees = cur.fetchall()
                employees_list=[(employee['Fname'] + " " + employee['Lname']) for employee in employees]
                employees_list.insert(0,"")
                form.emergency_contact_employee.choices = employees_list

                if form.validate_on_submit():
                        fname = form.emergency_contact_employee.data.split(" ")[0]
                        lname = form.emergency_contact_employee.data.split(" ")[1]
                        query = '''
                                SELECT E.EmployeeID
                                FROM Employee E
                                WHERE Fname = ? AND Lname = ? 
                                '''
                        cur.execute(query,(fname,lname))
                        ID = cur.fetchall()[0]['EmployeeID']
                        
                        # format phone number to: (xxx) xxx-xxxx
                        tmp = form.emergency_contact_phone.data
                        first = tmp[0:3]
                        second = tmp[3:6]
                        third = tmp[6:10]
                        format_number = "(" + first + ") " + second + "-" + third

                        query = '''
                                INSERT INTO EmergencyContact VALUES(?,?,?,?) 
                                '''
                        cur.execute(query, (form.emergency_contact_name.data, format_number , 
                                             form.emergency_contact_relation.data, ID))
                        
                        conn.commit()
                        cur.close()

                        flash(f'{form.emergency_contact_name.data}: added as Emergency Contact for {form.emergency_contact_employee.data}', 'success')
                        return redirect(url_for('add_emergency_contact'))


                return(render_template('add_emergency_contact.html', form = form))

        
        @app.route('/delete_emergency_contact', methods=['GET', 'POST'])
        def delete_emergency_contact():
                form = RemoveContactForm()
                connection = sqlite3.connect("instance/flaskr.sqlite")
                connection.row_factory = dict_factory
                cur = connection.cursor()
                cur.execute("PRAGMA foreign_keys=on")

                # get emergency contact info
                cur.execute('''
                                SELECT EC.ContactName, EC.PhoneNumber, 
                                EC.Relation, E.Fname, E.Lname
                                FROM EmergencyContact EC, Employee E 
                                WHERE EC.ID = E.EmployeeID 
                                ORDER BY E.Lname, E.Fname ASC
                        ''')
                emergency_contacts = cur.fetchall()

                if form.validate_on_submit():
                        selected_contacts = request.form.getlist('chk')

                        #loop over selected employees removing each one
                        for c in selected_contacts:
                                contact_name = c.split("+")[0]
                                employee_Fname = c.split("+")[1]
                                employee_Lname = c.split("+")[2]

                                # find the ID to remove
                                query = "SELECT E.EmployeeID FROM Employee E WHERE E.Fname = ? AND E.Lname =?"
                                cur.execute(query,(employee_Fname, employee_Lname))
                                ID = cur.fetchall()[0]['EmployeeID']
                                print(ID)
                                # delete contact
                                query = '''DELETE FROM EmergencyContact 
                                        WHERE ContactName = ? AND ID = ?  '''
                                cur.execute(query,(contact_name, ID))


                        connection.commit()
                        cur.close()
                        
                        return(redirect(url_for('emergency')))

                return(render_template('delete_emergency_contact.html', form = form, emergency_contacts = emergency_contacts))



        from . import db
        db.init_app(app)

        return(app)