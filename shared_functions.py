import os
import sqlite3
from datetime import datetime, date


from flask import Flask, render_template, url_for, flash, redirect, request
from forms import NewEmployeeForm, update_employee_info_form, RemoveEmployeeForm, UpdateEmployeeFilloutFrom ,PayrollForm, ContactForm, RemoveContactForm, Add_shift_form, get_shifts_form, GeneratePayStub
from wtforms.fields import Label 

from decimal import *

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

'''
This module contains functions encapsulating frequently used operations.
This module is shared between all created Blueprints 
'''

TODAYS_DATE = datetime.today().strftime('%Y-%m-%d')

#Turn the results from the database into a dictionary
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
        

def getEmployeeID(fname,lname):
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    query = ''' SELECT EmployeeID
                        FROM Employee
                        WHERE Fname = ? AND Lname = ?''' 

    cur.execute(query,(fname,lname))
    employee_id = cur.fetchall()[0]['EmployeeID']
    conn.commit()
    cur.close()
            
    return employee_id

def get_department_and_pay_from_employee_id(employee_id):
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")
    query = ''' SELECT *
                FROM Employee E, Office Of
                WHERE E.EmployeeID = ? and E.EmployeeID = Of.ID ''' 

    cur.execute(query,(employee_id))
    records = cur.fetchall()

    if len(records) == 0:
        query = ''' SELECT *
                FROM Employee E, Operations Op
                WHERE E.EmployeeID = ? and E.EmployeeID = Op.ID ''' 

        cur.execute(query,(employee_id))
        records = cur.fetchall()
        department_and_pay = ('operations', records[0]['WagePerHour'])
    else:
        department_and_pay = ('office', records[0]['Salary'])

    conn.commit()
    cur.close()
    return department_and_pay

def get_total_hours_from_shifts(employee_id, start, end):
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")
    query = ''' SELECT *
                FROM Employee E, Shift S
                WHERE E.EmployeeID = ? and E.EmployeeID = S.ID and S.DateofShift BETWEEN ? and ? ''' 

    cur.execute(query,(employee_id, start, end))
    records = cur.fetchall()

    total_hours = 0
    
    for r in records:
        total_hours += abs(r['EndTime'] - r['StartTime'])

    conn.commit()
    cur.close()
    return total_hours


def getPeriodIncome(Id, c):
    # calculate income for period
    query = '''SELECT Salary FROM Office      
                    WHERE ID = ?'''         
    c.execute(query, (Id)) 
    income = c.fetchall()

    print(income)
    getcontext().prec = 2
    if not income:
        #employee is paid per hour
        query = '''SELECT WagePerHour FROM Operations      
                        WHERE ID = ?'''         
        c.execute(query, (Id)) 
        income = c.fetchall()
        ammount = income[0]['WagePerHour']
        ammount = Decimal(ammount)*Decimal(50)
    else:
        ammount = Decimal(income[0]['Salary'])/Decimal(24)
    
    return ammount