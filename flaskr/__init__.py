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
from emergency import emergency_pages
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
        
        # define shared modules 
        app.register_blueprint(shift_pages)     # shifts.py
        app.register_blueprint(employee_pages)  # employees.py
        app.register_blueprint(payroll_pages)   # payroll.py
        app.register_blueprint(emergency_pages) # emergency.py
        
        @app.route('/')
        def index():
                
                print (sys.path)
                return render_template('index.html')



        



        from . import db
        db.init_app(app)

        return(app)