/* needed for sqlite to recognize foreign keys*/
PRAGMA foreign_keys=on;

CREATE TABLE Employee(
    EmployeeID char(7) NOT NULL,
    SIN int(9) NOT NULL,
    DateofBirth DATE NOT NULL,
    DateofHire DATE NOT NULL,
    Fname CHARACTER(100) NOT NULL, 
    Mname CHARACTER(100) ,
    Lname CHARACTER(100) NOT NULL,
    Address CHARACTER(100) NOT NULL,
    PRIMARY KEY (EmployeeID)
    );
   
CREATE TABLE EmergencyContact(
    ContactName CHARACTER(100) NOT NULL,
    PhoneNumber char(20) NOT NULL,
    Relation CHARACTER(100) NOT NULL,
    ID CHARACTER(7) NOT NULL,
    PRIMARY KEY (ContactName, ID),
    FOREIGN KEY (ID) REFERENCES Employee(EmployeeID)
    ON DELETE CASCADE
  );
    
CREATE TABLE Office(
    ID char(7) NOT NULL,
    Salary int(9) NOT NULL,
    PRIMARY KEY (ID),
    FOREIGN KEY (ID) REFERENCES Employee(EmployeeID)
    ON DELETE CASCADE
    );
    
CREATE TABLE Operations(
    ID char(7) NOT NULL,
    WagePerHour DECIMAL(9) NOT NULL,
    PRIMARY KEY (ID),
    FOREIGN KEY (ID) REFERENCES Employee(EmployeeID)
    ON DELETE CASCADE
    );

CREATE TABLE Payroll(
    ChequeNumber int(10) NOT NULL,
    PayrollDate DATE NOT NULL,
    GrossPay DECIMAL NOT NULL,
    CPP DECIMAL NOT NULL,
    EI DECIMAL NOT NULL,
    FederalTax DECIMAL NOT NULL,
    ProvincialTax DECIMAL NOT NULL,
    YTDGP DECIMAL (6,4) NOT NULL,
    YTDCPP DECIMAL (6,4) NOT NULL,
    YTDEI DECIMAL (6,4) NOT NULL,
    YTDNET DECIMAL (6,4) NOT NULL,
    YTDFedTax DECIMAL (6,4) NOT NULL,
    YTDProvTax DECIMAL (6,4) NOT NULL,
    RegHours DECIMAL(4,2) NOT NULL,
    OTHours DECIMAL(4,2),
    StatHours DECIMAL (4,2),
    ID char(7) NOT NULL,
    PRIMARY KEY (ChequeNumber),
    FOREIGN KEY (ID) REFERENCES Employee(EmployeeID)
    ON DELETE CASCADE
    );

CREATE TABLE Shift(
	ID CHAR(10) NOT NULL,
    ShiftID CHAR(10) NOT NULL,
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    DateofShift DATE NOT NULL,
    RoundedStartTime TIME NOT NULL,
    RoundedEndTime TIME NOT NULL,
    PRIMARY KEY (ShiftID),
    FOREIGN KEY (ID) REFERENCES Employee(EmployeeID)
    ON DELETE CASCADE
    );

CREATE TABLE Phone(
    PhoneNumber CHAR(20) NOT NULL,
    ID char(7) NOT NULL,
    PRIMARY KEY(PhoneNumber, ID),
    FOREIGN KEY (ID) REFERENCES Employee(EmployeeID)
    ON DELETE CASCADE
);


/*------------------------------------ Initial Values ------------------------------------------*/


INSERT INTO Employee (EmployeeID, SIN, DateofBirth, DateofHire, Fname, Mname, Lname, Address)
VALUES (0001, 897586446, '1987-01-09', '2018-04-26', 'Jack', 'Young', 'Ma', '8990 Alpha Street'),
	   (0002, 397486256, '1987-04-28', '2010-03-23', 'Emma', 'Yye', 'Zhang', '8990 Beta Street'),
	   (0003, 296586884, '1980-09-01', '2012-05-16', 'Alan', 'Zhu', 'Kit', '1990 Nova Street'),
	   (0004, 697086464, '1970-03-21', '2013-01-04', 'Wilson', 'Stephan', 'Kit', '3090 Crew Street'),
       (0005, 197526335, '1990-02-09', '2015-07-07', 'Sharon', 'Yao', 'Wang', '1990 Walter Street');


INSERT INTO EmergencyContact  (ContactName, PhoneNumber, Relation, ID)
VALUES ('Belle Lu', '(889) 908-1728','Sister',0001),
       ('Wang Zhu', '(883) 902-1123','Wife',0002),
       ('Ling Che', '(183) 202-1098','Cousin',0003),
       ('Lee Hwang','(113) 204-1323','Friend',0004),
       ('Christopher Wayne','(522) 041-3623','Father',0005);


INSERT INTO Office (ID, Salary)
VALUES (0001, 60000),
       (0002, 50000);

INSERT INTO Operations(ID, WagePerHour)
VALUES (0003, 20),
       (0004, 18),
       (0005, 17);


INSERT INTO Phone(PhoneNumber, ID)
VALUES ('(778) 789-5645', 0001),
       ('(604) 512-3695', 0002),
	   ('(778) 956-1234', 0003),
	   ('(778) 456-1293', 0004),
	   ('(778) 236-1290', 0005);


INSERT INTO Shift(ID, ShiftID, StartTime, EndTime, DateofShift, 
                  RoundedStartTime, RoundedEndTime)
VALUES(0003,100,'16:30:32','20:25:46','2021-01-01', '16:30:00','20:30:00'),
      (0003,101,'16:30:32','20:25:46','2021-01-01', '16:30:00','20:30:00'),
      (0003,102,'16:30:32','20:25:46','2021-01-03', '16:30:00','20:30:00'),
      (0003,103,'16:30:32','20:25:46','2021-01-05', '16:30:00','20:30:00'),
      (0003,104,'16:30:32','20:25:46','2021-01-06', '16:30:00','20:30:00'),
      (0003,105,'16:30:32','20:25:46','2021-01-07', '16:30:00','20:30:00'),
      (0003,106,'16:30:32','20:25:46','2021-01-10', '16:30:00','20:30:00'),
      (0003,107,'16:30:32','20:25:46','2021-01-12', '16:30:00','20:30:00'),
      (0003,108,'16:30:32','20:25:46','2021-01-19', '16:30:00','20:30:00'),
      (0003,109,'16:30:32','20:25:46','2021-01-24', '16:30:00','20:30:00');

