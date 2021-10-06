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

    if (TODAYS_DATE[-2:] == '15'):
        # Process only operations employees on the 15th
        generate_all = False
    else:
        generate_all = True
    
    conn = sqlite3.connect("instance/flaskr.sqlite")
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=on")

    # seperate operations and office employees for processing
    cur.execute(''' SELECT E.*, O.WagePerHour FROM Employee E, Operations O
                    WHERE E.ID = O.ID''')
    operations_employees = cur.fetchall()
    cur.execute(''' SELECT E.*, O.Salary FROM Employee E, Office O
                    WHERE E.ID = O.ID''')
    office_employees = cur.fetchall()

    employees_list=[(employee['Fname'] + " " + employee['Lname']) for employee in office_employees+operations_employees]
   
    form_generate_stubs = GeneratePayStub()
    form_display_stubs = PayrollForm()
    form_display_stubs.employee_filter.choices = [" "] + employees_list
    form_generate_stubs.employee_filter_pay_stub.choices = ["ALL"] + employees_list

    if form_generate_stubs.validate_on_submit():
        if (form_display_stubs.employee_filter.data == "ALL"):
            # Generate all possible paystubs

            for employee in operations_employees:
                # Generate stubs for operations employees
                employee_id = employee['ID']
                wage = employee['WagePerHour']
                query = '''SELECT PayrollDate FROM Payroll
                        ORDER BY PayrollDate desc '''
                cur.execute(query)

                last_period = cur.fetchone()
                if (last_period is None):
                    last_period = '0000-01-01'
                else:
                    last_period = last_period['PayrollDate']

                print(f'last period start date {last_period}')
                cur.execute('''SELECT date(?, '+1 day') as date''',[last_period])
                last_period = cur.fetchone()['date']
                print(f'last period start date +1 day {last_period}')

                grossPay = getPeriodIncome(employee_id, wage, last_period, TODAYS_DATE, cur)
                print(grossPay)
                full_name = getName(employee_id, cur)
                print(f'{full_name} gross income for period ({TODAYS_DATE}) : {grossPay}')

                '''
                cur.execute("Select MAX(ChequeNumber) From Payroll")
                new_cheque_number = cur.fetchall()
                if (new_cheque_number[0]['MAX(ChequeNumber)'] is None):
                    new_cheque_number = 0000000
                else:
                    new_cheque_number = int(new_cheque_number[0]['MAX(ChequeNumber)'])+1
                '''
            if (generate_all):
                # Genrate stubs for office employees aswell
                for employee in office_employees:
                    employee_id = employee['ID']
                    salary = employee['Salary']
                    grossPay = salary/12
                    full_name = getName(employee_id, cur)
                    print(f'{full_name} gross income for period ({TODAYS_DATE}) : {grossPay}')
        else:
            # generate pay stub for the specified employee
            print("Generate specific stub")
    
        flash(f'Pay stubs generated for Pay Period: {TODAYS_DATE}', 'success')

    elif form_display_stubs.validate_on_submit():
        # Display pay stubs
        fname = form_display_stubs.employee_filter.data.split(" ")[0]
        lname = form_display_stubs.employee_filter.data.split(" ")[1]
        ID = getEmployeeID(fname, lname, cur)

        # get pay stubs
        query = '''SELECT * 
                FROM Employee E, Payroll P
                WHERE P.ID = ? AND E.ID = P.ID AND P.PayrollDate between ? and ? 
                Order by P.PayrollDate desc
                LIMIT ?'''
        
        # check which filter is selected
        if (form_display_stubs.payroll_date_range.data == "YTD"):
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
    return render_template('payroll.html', form = form_display_stubs, generate_pay_stub_form = form_generate_stubs)

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
    c.execute("SELECT Fname, Mname, Lname, ID FROM Employee")
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
        ammount = getPeriodIncome(e['ID'], c)
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