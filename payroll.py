# This module encapsulates all the pages related to payroll and tax information
# This module contains the function used to automate the tax calculation

from datetime import datetime
from flask import render_template, request,Blueprint, flash
from forms import PayrollForm, GeneratePayStub
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from shared_functions import *

payroll_pages = Blueprint('payroll_pages', __name__)
FEDERAL_PDOC = "https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/payroll-deductions-online-calculator.html"


@payroll_pages.route('/report')
def report():
    return render_template('report.html')



def getGrossPay(cur, employee, department):
    full_name = employee['Fname'] + " " + employee['Lname']
    employee_id = employee['ID']
    if department == 'OP': 
        # Generate stub for operations employee
        wage = employee['WagePerHour']
        query = '''SELECT PayrollDate FROM Payroll
                ORDER BY PayrollDate desc '''
        cur.execute(query)

        # get the date of the last period to calculate gross income for the period
        last_period = cur.fetchone()
        if (last_period is None):
            last_period = '0000-01-01'
        else:
            last_period = last_period['PayrollDate']

        # don't include hours worked on the date of the last period
        cur.execute('''SELECT date(?, '+1 day') as date''',[last_period])
        last_period = cur.fetchone()['date']
        gross_pay = getPeriodIncome(employee_id, wage, last_period, TODAYS_DATE, cur)
        
        '''
        cur.execute("Select MAX(ChequeNumber) From Payroll")
        new_cheque_number = cur.fetchall()
        if (new_cheque_number[0]['MAX(ChequeNumber)'] is None):
            new_cheque_number = 0000000
        else:
            new_cheque_number = int(new_cheque_number[0]['MAX(ChequeNumber)'])+1
        '''
    elif department == 'OF':
        # Genrate stubs for office employees aswell
        salary = employee['Salary']
        gross_pay = salary/12

    return gross_pay



def openWebsite(url):
    # open url in browser
    driver = webdriver.Firefox()
    driver.get(url)
     # 'I accept' button
    accept = "https://apps.cra-arc.gc.ca/ebci/rhpd/prot/welcome.action?request_locale=en_CA"
    # skip the first 2 pages 
    driver.find_element_by_xpath('//a[@href="'+accept+'"]').click()
    driver.find_element_by_id('welcome_button_next').click()
    print(f"Browser opened at url: {url}")
    return driver



def closeWebsite(driver):
    driver.close()
    print('Browser closed')
    return




def calculateTax(driver, name, period_gross, frequency):
    # PAGE 1
    # name 
    field_name = driver.find_element_by_name("employeeName")
    field_name.clear()
    field_name.send_keys(name)

    # province -> BC
    prov = Select(driver.find_element_by_name("jurisdiction"))
    prov.select_by_index(2)

    # pay frequency
    pay_freq = Select(driver.find_element_by_name("payPeriodFrequency"))
    if frequency == 'semi-monthly':
        pay_freq.select_by_value('SEMI_MONTHLY')
    elif frequency == 'monthly':
        pay_freq.select_by_value('MONTHLY_12PP')

    #date 
    Select(driver.find_element_by_name("datePaidDay")).select_by_index(datetime.today().day)
    Select(driver.find_element_by_name("datePaidMonth")).select_by_index(datetime.today().month)
    Select(driver.find_element_by_name("datePaidYear")).select_by_index(1)
    driver.find_element_by_id("payrollDeductionsStep1_button_next").click()

    # PAGE 2
    # gross income per period
    gross_income = driver.find_element_by_id("incomeAmount")
    gross_income.clear()
    gross_income.send_keys("{:.2f}".format(period_gross))
    driver.find_element_by_id("payrollDeductionsStep2a_button_next").click()
    
    # PAGE 3
    driver.find_element_by_id("payrollDeductionsStep3_button_calculate").click()
    
    # Results Page 
    fed_tax = driver.find_element_by_xpath("//table/tbody/tr[6]/td[2]").text
    prov_tax = driver.find_element_by_xpath("//table/tbody/tr[7]/td[2]").text
    cpp = driver.find_element_by_xpath("//table/tbody/tr[9]/td[3]").text
    ei = driver.find_element_by_xpath("//table/tbody/tr[10]/td[3]").text
    net_pay = driver.find_element_by_xpath("//table/tbody/tr[12]/td[4]").text

    print(f'----Calculated tax info for {name}----')
    print("Gross pay: {:.2f}".format(period_gross))
    print(f'FED: {fed_tax}\nProv: {prov_tax}\nCPP: {cpp} \nEI:  {ei}\nNet Pay: {net_pay}')
    print(f'Total tax deductions: {fed_tax + prov_tax}\nTotal deductions: {fed_tax + prov_tax + ei + cpp}')
    print("-"*10)

    driver.find_element_by_id("payrollDeductionsResults_button_nextCalculationButton").click()
    return fed_tax, prov_tax, cpp, ei, net_pay

        
@payroll_pages.route('/report/payroll', methods=['GET', 'POST'])
def payroll():
    global TODAYS_DATE
    cur, conn = openDatabase()
    
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

    if (form_generate_stubs.is_submitted() & ('generate_pay_stubs' in request.form)):
        driver = openWebsite(FEDERAL_PDOC)

        for employee in operations_employees:
            gross_pay = getGrossPay(cur, employee, 'OP')
            name = employee['Fname'] + " " + employee['Lname']
            if gross_pay > 0 :
                pay_frequency = 'semi-monthly'
                fed_tax, prov_tax, cpp, ei, net_pay = calculateTax(driver, name , gross_pay, pay_frequency)
            else:
                print(f"failed to calculate {name}'s tax information: Gross pay cannot be $0")
            
        
        # only generate office employees (monthly pay frequency) pay stubs on the last day of the month
        if (TODAYS_DATE[-2:] != '15'):
            for employee in office_employees:
                gross_pay = getGrossPay(cur, employee, 'OF')
                name = employee['Fname'] + " " + employee['Lname']
                if gross_pay > 0 :
                    pay_frequency = 'monthly'
                    fed_tax, prov_tax, cpp, ei, net_pay = calculateTax(driver, name, gross_pay, pay_frequency)
                else:
                    print(f"failed to calculate {name}'s tax information: Gross pay cannot be $0")
               
        closeWebsite(driver)
        

    elif form_display_stubs.validate_on_submit() & ('display_pay_stubs' in request.form):
        # Display pay stubs
        fname = form_display_stubs.employee_filter.data.split(" ")[0]
        lname = form_display_stubs.employee_filter.data.split(" ")[1]
        employee_id = getEmployeeID(fname, lname, cur)
        if employee_id == -1 :
            flash('Please select the employee you would like to generate pay stubs for', 'danger')
        else:
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
            cur.execute(query, (employee_id, start ,end ,limit))
            stubs = cur.fetchall()

            
            closeDatabase(cur, conn)
            return render_template('payroll_data.html', stubs = stubs) 
    
    closeDatabase(cur, conn)
    return render_template('payroll.html', form_display_stubs = form_display_stubs, form_generate_stubs = form_generate_stubs)


