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

employee_pages = Blueprint('employee_pages', __name__)

@employee_pages.route('/employee', methods=['GET', 'POST'])
def employee():
    return render_template('employee.html')

@employee_pages.route('/employee/add_new_employee', methods=['GET', 'POST'])
def add_new_employee():
    form=NewEmployeeForm()
    global TODAYS_DATE 

    if form.validate_on_submit():
            
        if(len(form.employee_middle_name.data) == 0):
            # no middle name
            form.employee_middle_name.data = "NULL"
        
        conn = sqlite3.connect("instance/flaskr.sqlite")
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys=on")

        #use next available ID
        c.execute('''
                SELECT MAX(EmployeeID)
                FROM Employee
                '''
                )
        Employee_id_dict = list(c.fetchall())
        EMPLOYEE_ID = str(int(Employee_id_dict[0][0]) + 1)
        
        
        #Add the new employee into the 'Employee' table
        query = '''insert into Employee VALUES (?, ?, ?, ?, ?, ?, ?,?)'''
        c.execute(query, (EMPLOYEE_ID,
                form.employee_SIN.data,
                form.employee_date_of_birth.data,
                TODAYS_DATE,
                form.employee_first_name.data,
                form.employee_middle_name.data,
                form.employee_last_name.data,
                form.employee_Address.data))

        print("role = " + form.employee_role.data)
        if (form.employee_role.data == "Office"):
            # add to office table
            print("OFFICE!!")
            query = '''insert into Office VALUES (?, ?)'''
            c.execute(query, (EMPLOYEE_ID, int(form.employee_salary.data)))
        
        else:
            # add to operations table
            print("OPERATIONS!!")
            query = 'insert into Operations VALUES (?, ?)'
            c.execute(query, (EMPLOYEE_ID, float(form.employee_salary.data)))


        # format phone number to: (xxx) xxx-xxxx
        tmp = form.employee_phone.data
        first = tmp[0:3]
        second = tmp[3:6]
        third = tmp[6:10]
        format_number = "(" + first + ") " + second + "-" + third
        

        # Add their Phone Number
        query = 'insert into Phone values (?,?)'
        c.execute(query, (format_number, EMPLOYEE_ID) )


        conn.commit()
        c.close()

        flash(f'{form.employee_first_name.data} {form.employee_last_name.data}: added to database', 'success')
        return redirect(url_for('employee_pages.add_new_employee'))

    return render_template('add_new_employee.html',form=form)



@employee_pages.route('/employee/update_employee_info', methods=['GET', 'POST'])
def update_employee_info():
    drop_down_form = update_employee_info_form()

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
    drop_down_form.employee_update.choices = employees_list

    if drop_down_form.validate_on_submit():

        fname = drop_down_form.employee_update.data.split(" ")[0]
        lname = drop_down_form.employee_update.data.split(" ")[1]

        conn.commit()
        cur.close()

        return redirect(url_for('employee_pages.update_fill_out', fname = fname , lname = lname))
            
    
    conn.commit()
    cur.close()
    return render_template('update_employee_info.html',form=drop_down_form)

        
@employee_pages.route('/update_fill_out/<fname>/<lname>', methods=['GET', 'POST'])
def update_fill_out(fname , lname):
    update_form = UpdateEmployeeFilloutFrom()

    # open database connection
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")

    # get the ID for the selected employee
    query = '''
            SELECT E.EmployeeID
            FROM Employee E
            WHERE Fname = ? AND Lname = ? 
            '''
    cur.execute(query,(fname,lname))
    tmp = cur.fetchall()
    ID = tmp [0]['EmployeeID']
  
    # get the employee's info 
    query = '''SELECT *, PhoneNumber FROM Employee, Phone 
                WHERE EmployeeID = ? AND Phone.ID = Employee.EmployeeID'''
    cur.execute(query , (ID))
    current_vals = cur.fetchall()

    # display current values 
    update_form.employee_Address.label.text = str(current_vals[0]['Address'])
    update_form.employee_first_name.label.text = fname
    update_form.employee_middle_name.label.text = str(current_vals[0]['Mname'])
    update_form.employee_last_name.label.text = lname
    update_form.employee_SIN.label.text = str(current_vals[0]['SIN'])
    update_form.employee_phone.label.text = str(current_vals[0]['PhoneNumber'])
    update_form.employee_date_of_birth.label.text = str(current_vals[0]['DateofBirth'])
    update_form.employee_first_name.label.text = fname
    

    # query the Office table to see what department the employee is in
    query = "SELECT * FROM Office WHERE ID = ?"
    cur.execute(query,(ID))
    Department = cur.fetchall()

    # query is empty, employee is in operations
    if(len(Department) == 0):
        d_name = 'Operations'
        update_form.employee_role.label.text = 'Operations'
        update_form.employee_role.choices = ['Operations', 'Office']
        cur.execute("SELECT WagePerHour From Operations Where ID = ?", (ID))
        wage = cur.fetchall()[0]['WagePerHour']
        update_form.employee_salary.label.text = wage
    else:
        d_name = 'Office'
        update_form.employee_role.label.text= 'Office'
        update_form.employee_role.choices = ['Office', 'Operations']
        update_form.employee_salary.label.text = Department[0]['Salary']

    full_name = fname + " " + lname 

    if update_form.validate_on_submit():
        # check which fields have changed and update them
        
        if (len(update_form.employee_SIN.data) != 0):
            cur.execute("Update Employee SET SIN = ? WHERE EmployeeID = ?" ,( update_form.employee_SIN.data, ID))
        if (len(update_form.employee_date_of_birth.data) != 0):
            cur.execute("Update Employee SET DateofBirth = ? WHERE EmployeeID = ?" , (update_form.employee_date_of_birth.data , ID))
        if (len(update_form.employee_first_name.data) != 0):
            cur.execute("Update Employee SET Fname = ? WHERE EmployeeID = ?" , (update_form.employee_first_name.data, ID))
        if (len(update_form.employee_last_name.data) != 0):
            cur.execute("Update Employee SET Lname = ? WHERE EmployeeID = ?" ,( update_form.employee_last_name.data, ID))
        if (len(update_form.employee_middle_name.data) != 0):
            cur.execute("Update Employee SET Mname = ? WHERE EmployeeID = ?" , (update_form.employee_middle_name.data, ID))
        if (len(update_form.employee_Address.data) != 0):
            cur.execute("Update Employee SET Address = ? WHERE EmployeeID = ?" , (update_form.employee_Address.data, ID))
        if (len(update_form.employee_phone.data) != 0):
            # format phone number before adding to DB
            tmp = update_form.employee_phone.data
            first = tmp[0:3]
            second = tmp[3:6]
            third = tmp[6:10]
            format_number = "(" + first + ") " + second + "-" + third
            cur.execute("UPDATE Phone SET PhoneNumber = ? WHERE ID = ?", (format_number, ID) )

        # reflect changes in Operations and Office tables 
        # if statemeants are used because SQL Tables can not be variables
        if( len(update_form.employee_salary.data) != 0 ):
            if (d_name == "Operations"):
                query = "DELETE FROM Operations WHERE ID = ?"
                cur.execute(query, (ID))
                

                if (update_form.employee_role.data == 'Office'):
                    query = "INSERT INTO Office VALUES(?, ?)"
                    cur.execute(query, (ID ,update_form.employee_salary.data))
                else:
                    query = "INSERT INTO Operations VALUES(?, ?)"
                    cur.execute(query, (ID ,update_form.employee_salary.data))
                            
            else:
                query = "DELETE FROM Office WHERE ID = ?"
                cur.execute(query, (ID))
            
                if (update_form.employee_role.data == 'Office'):
                    query = "INSERT INTO Office VALUES(?, ?)"
                    cur.execute(query, (ID ,update_form.employee_salary.data))
                else:
                    query = "INSERT INTO Operations VALUES(?, ?)"
                    cur.execute(query, (ID ,update_form.employee_salary.data))


        conn.commit()
        cur.close()
        return(redirect(url_for('employee_pages.update_employee_info')))


    conn.commit()
    cur.close()

    return render_template('update_fill_out.html', form = update_form, name = full_name)#, form = form, name = name)



@employee_pages.route('/employee/remove_employee', methods=['GET', 'POST'])
def removeEmployee():
    form = RemoveEmployeeForm()
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")
    # list all employees
    cur.execute('''
                    SELECT E1.*
                    FROM Operations O, Employee E1
                    WHERE O.ID = E1.EmployeeID
                    UNION
                    SELECT E2.*
                    FROM Office Of, Employee E2
                    WHERE Of.ID = E2.EmployeeID
                    ORDER BY E2.Lname ASC

            ''')
    employees = cur.fetchall()

    if form.validate_on_submit():
        selected_employees = request.form.getlist('chkb')
        for e in selected_employees:
                #remove selected employees 
                query = "DELETE FROM Employee WHERE EmployeeID = ?"
                print("remove ID: " +str(e) +" from Employee")
                cur.execute(query,(e))

        
        conn.commit()
        cur.close()
        return redirect(url_for('employee_pages.removeEmployee'))
    
    return render_template('removeEmployee.html', form=form, employees = employees)

@employee_pages.route('/report/employeeinfo', methods=['GET', 'POST'])
def employeeinfo():
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")
    # display operations employees
    cur.execute('''
            SELECT E.*, P.PhoneNumber, O.WagePerHour
            FROM Operations O, Employee E, Phone P
            WHERE O.ID = E.EmployeeID AND P.ID = E.EmployeeID AND O.ID = P.ID
            ORDER BY UPPER(E.Lname) ASC
                    ''')
    operations = cur.fetchall()

    #display office employees
    cur.execute('''
            SELECT E.*, P.PhoneNumber, O.Salary  
            FROM Office O, Employee E, Phone P
            WHERE O.ID = E.EmployeeID AND P.ID = E.EmployeeID AND O.ID = P.ID
            ORDER BY UPPER(E.Lname) ASC
                    ''')
    offices = cur.fetchall()
    
    conn.commit()
    cur.close()

    return render_template('employeeinfo.html', operations=operations, offices=offices,
                            office_len=len(offices), operations_len=len(operations))
