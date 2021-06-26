import os
import sqlite3
from datetime import datetime, date


from flask import Flask, render_template, url_for, flash, redirect, request,Blueprint
from forms import NewEmployeeForm, update_employee_info_form, RemoveEmployeeForm, UpdateEmployeeFilloutFrom ,PayrollForm, ContactForm, RemoveContactForm, Add_shift_form, get_shifts_form, GeneratePayStub
from wtforms.fields import Label 

from decimal import *

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from shared_functions import *

shift_pages = Blueprint('shift_pages', __name__)


@shift_pages.route('/shift', methods=['GET', 'POST'])
def shift():
    return render_template('shift.html')

@shift_pages.route('/shift/timecard', methods=['GET', 'POST'])
def timecard():
    form = get_shifts_form()
    # Populate drop down dynamically
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")
    cur.execute(''' SELECT EmployeeID, Fname, Lname FROM Employee''')
    employees = cur.fetchall()
    employees_list=[(employee['Fname'] + " " + employee['Lname']) for employee in employees]
    employees_list.insert(0,"")
    form.employee_filter.choices = employees_list
    if form.validate_on_submit():
        employee_full_name = form.employee_filter.data
        fname = form.employee_filter.data.split(" ")[0]
        lname = form.employee_filter.data.split(" ")[1]
        emloyee_id=getEmployeeID(fname,lname)

        query ='SELECT * FROM Shift WHERE ID = ?'
        cur.execute(query, (emloyee_id,))
        shifts=cur.fetchall()
        conn.commit()
        cur.close()
        return render_template('timecard_data.html',shifts=shifts, employee_full_name=employee_full_name)
            
            
    return render_template('timecard.html', form=form)


@shift_pages.route('/shift/add_shift', methods=['GET', 'POST'])
def add_shift():
    form = Add_shift_form()
        # Populate drop down dynamically
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")
    cur.execute(''' SELECT EmployeeID, Fname, Lname FROM Employee''')
    employees = cur.fetchall()
    employees_list=[(employee['Fname'] + " " + employee['Lname']) for employee in employees]
    employees_list.insert(0,"")
    form.employee_filter.choices = employees_list
    if form.validate_on_submit():
        # calculating the next shift id to be added
        cur.execute('''
                SELECT MAX(ShiftID)
                FROM Shift
                '''
                )
        Shift_ID_dictionary = cur.fetchall()
        max_shift_id = Shift_ID_dictionary[0]['MAX(ShiftID)']
        next_shift_id_to_be_added = str(int(max_shift_id)+1)
        # calculating employee id from fname and lastname
        fname = form.employee_filter.data.split(" ")[0]
        lname = form.employee_filter.data.split(" ")[1]
        emloyee_id=getEmployeeID(fname,lname)
        # Now that we have shiftID and employeeID we can generate the new shift
        query = 'insert into Shift VALUES (?, ?, ?, ?, ?)'
        cur.execute(query, (emloyee_id,next_shift_id_to_be_added,form.shift_start_time.data,form.sift_end_time.data,form.date_of_shift.data))
        conn.commit()
        cur.close()

        flash(f'Shift {next_shift_id_to_be_added} was added for {fname} {lname}', 'success')
        return redirect(url_for('shift_pages.add_shift'))
    return render_template('add_shift.html', form=form)