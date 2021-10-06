import decimal
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
        

def getEmployeeID(fname,lname, cur):
    query = ''' SELECT ID FROM Employee
                WHERE Fname = ? AND Lname = ?''' 
    cur.execute(query,(fname,lname))
    employee_id = cur.fetchall()[0]['ID']
    return employee_id

def getName(id , cur):
    cur.execute('''SELECT Fname, Lname FROM Employee E WHERE E.ID = ?''', (id))
    name = cur.fetchone()
    full_name = name['Fname'] + " " + name['Lname']
    return(full_name)

def getPeriodIncome(Id, wage, start, end , cur):
    # calculate income for period between start and end (inclusive)
    # ammount = [regular hours * regular rate] + [OT hours * (regular_rate + regular_rate/2)]

    ammount = 0
    getcontext().prec = 2
    query = '''SELECT sum(S.HoursWBreak) as RegHours, sum(S.OTHours) as OTHours FROM Shift S
               WHERE S.ID = ? AND S.DateofShift Between ? AND ?'''
    cur.execute(query, (Id, start, end))
    hours = cur.fetchone()
    
    if(hours['RegHours'] is not None):
        ammount += hours['RegHours'] * wage
    if(hours['OTHours'] is not None):
        ammount +=  hours['OTHours'] * (wage + (decimal(wage)/2))
        print(ammount)

    return ammount