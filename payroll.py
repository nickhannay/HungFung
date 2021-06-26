# This module encapsulates all the pages related to payroll and tax information
# This module contains the function used to automate the tax calculation

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

payroll_pages = Blueprint('payroll_pages', __name__)


@payroll_pages.route('/report')
def report():
    return render_template('report.html')

        
@payroll_pages.route('/report/payroll', methods=['GET', 'POST'])
def payroll():
    global TODAYS_DATE
    form = PayrollForm()
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")
    # Populate drop down dynamically
    cur.execute(''' SELECT EmployeeID, Fname, Lname FROM Employee''')
    employees = cur.fetchall()
    employees_list=[(employee['Fname'] + " " + employee['Lname']) for employee in employees]

    # drop down defaults to blank
    employees_list.insert(0,"")
    form.employee_filter.choices = employees_list
    generate_pay_stub_form = GeneratePayStub()
    generate_pay_stub_form.employee_filter_pay_stub.choices = employees_list

    if generate_pay_stub_form.validate_on_submit():
        fname = generate_pay_stub_form.employee_filter_pay_stub.data.split(" ")[0]
        lname = generate_pay_stub_form.employee_filter_pay_stub.data.split(" ")[1]
        employee_id = getEmployeeID(fname,lname)

        department, pay = get_department_and_pay_from_employee_id(employee_id)          # pay can be salary or wage
        start = generate_pay_stub_form.start_date.data
        end = generate_pay_stub_form.end_date.data
        num_days = abs((end - start).days)

        full_name = fname+' '+lname

        if department == 'office':
            total_pay = ((pay/12)/30)*num_days                                
        elif department == 'operations':
            total_hours_worked = get_total_hours_from_shifts(employee_id, start, end)
            total_pay = total_hours_worked*pay
        
        new_cheque_number_query = '''Select MAX(ChequeNumber) From Payroll'''
        cur.execute(new_cheque_number_query)
        new_cheque_number = cur.fetchall()
        

        if (new_cheque_number[0]['MAX(ChequeNumber)'] is None):
            new_cheque_number = 10000
        else:
            new_cheque_number = int(new_cheque_number[0]['MAX(ChequeNumber)'])+1

        insert_query = '''INSERT INTO Payroll VALUES (?,?,?,?,?,?,?,?,?,?,?,?)'''

        data_row = (new_cheque_number, TODAYS_DATE, total_pay, total_pay*0.02, total_pay*0.02, total_pay*0.12, total_pay*0.12, 1, 2, 3, 4, employee_id)
        cur.execute(insert_query, data_row)

        conn.commit()
        cur.close()
        flash('New Pay Stub Generated', 'success')

    elif form.validate_on_submit():
        # display pay stubs
        fname = form.employee_filter.data.split(" ")[0]
        lname = form.employee_filter.data.split(" ")[1]
        ID = getEmployeeID(fname, lname)

        # get pay stubs
        query = '''SELECT * 
                FROM Employee E, Payroll P
                WHERE P.ID = ? AND E.EmployeeID = P.ID AND P.PayrollDate between ? and ? 
                Order by P.PayrollDate desc
                LIMIT ?'''
        
        # check which filter is selected
        if (form.payroll_date_range.data == "YTD"):
            #Show pay stubs from start of year
            start = TODAYS_DATE[0:4] + "-01-01"
            end = TODAYS_DATE
            limit = 100
        else:
            #Show up to the last 25 stubs
            start = "2000-01-01"
            end = TODAYS_DATE
            limit = 25
        cur.execute(query, (ID, start ,end ,limit))
        stubs = cur.fetchall()

        
        conn.commit()
        cur.close()

        return render_template('payroll_data.html', stubs = stubs) 
    return render_template('payroll.html', form = form, generate_pay_stub_form = generate_pay_stub_form)

def navigateTaxSite(website):
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys=on")

    # open tax calculator in browser
    driver = webdriver.Firefox()
    driver.get(website)
    url = "https://apps.cra-arc.gc.ca/ebci/rhpd/prot/welcome.action?request_locale=en_CA"

    # skip the first 2 pages 
    driver.find_element_by_xpath('//a[@href="'+url+'"]').click()
    driver.find_element_by_id('welcome_button_next').click()
    
    #calculate info for each employee 
    c.execute("SELECT Fname, Mname, Lname, EmployeeID FROM Employee")
    employees = c.fetchall()
    for e in employees:
        # PAGE 1
        # name 
        name = driver.find_element_by_name("employeeName")
        name.clear()
        name.send_keys(e['Fname']+" "+e['Lname'])

        # province -> BC
        prov = Select(driver.find_element_by_name("jurisdiction"))
        prov.select_by_index(2)

        #pay period frequency -> semi-monthly
        pay_freq = Select(driver.find_element_by_name("payPeriodFrequency"))
        pay_freq.select_by_index(4)

        #date 
        Select(driver.find_element_by_name("datePaidDay")).select_by_index(datetime.today().day)
        Select(driver.find_element_by_name("datePaidMonth")).select_by_index(datetime.today().month)
        Select(driver.find_element_by_name("datePaidYear")).select_by_index(1)

        driver.find_element_by_id("payrollDeductionsStep1_button_next").click()

        # PAGE 2
        # gross income per period
        ammount = getPeriodIncome(e['EmployeeID'], c)
        gross_income = driver.find_element_by_id("incomeAmount")
        gross_income.clear()
        gross_income.send_keys("{:.2f}".format(ammount))
        driver.find_element_by_id("payrollDeductionsStep2a_button_next").click()
        
        # PAGE 3
        driver.find_element_by_id("payrollDeductionsStep3_button_calculate").click()
        
        # Results Page 
        fed_tax = driver.find_element_by_xpath("//table/tbody/tr[6]/td[2]").text
        prov_tax = driver.find_element_by_xpath("//table/tbody/tr[7]/td[2]").text
        CPP = driver.find_element_by_xpath("//table/tbody/tr[9]/td[3]").text
        EI = driver.find_element_by_xpath("//table/tbody/tr[10]/td[3]").text

        print(e['Fname']+" "+e['Lname'])
        print("FED: " + fed_tax)
        print("Prov: " + prov_tax)
        print("CPP: " + CPP)
        print("EI: "+ EI)
        print("-"*30)

        driver.find_element_by_id("payrollDeductionsResults_button_nextCalculationButton").click()
    
    driver.close()
    conn.commit()
    c.close()
    return

@payroll_pages.route('/report/tax', methods=['GET', 'POST'])
def tax():
    navigateTaxSite("https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/payroll-deductions-online-calculator.html")
    return render_template('tax.html')