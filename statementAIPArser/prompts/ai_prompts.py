"""
This file holds a set of reusable prompt strings for various AI assistants.
"""

GEMINI_STATEMENT_PARSE = """\

Please parse the attached financial statement PDF and a provide a csv response 

If the date is not clear parse the description data to infer

Any dates must be output in the format dd-mm-yyyy 

Only return a valid .csv, no other text or comments, CSV output should have the following structure

Date of transaction,Description of transaction,Amount of transaction,Direction, either paid in  or withdrawn,Balance remaining. 

There structure should be one transaction per row of CSV

Note that balance remaining may we be negative or overdrawn. possibly denoted with a minus sign or in brackets, or with an OD, or overdrawn. This must be represented in the banace reamining as a negative number

Note that no headers should be returned, just transaction data.

Provide exactly one row per transaction identified, do not skip any transactions

"""


GEMINI_PERSONAL_INFO_PARSE = """\


Please parse the attached financial statement PDF and a provide a JSON response consisting of personal data only, 
ignore any transaction data. The data required is as follows 

full name, address, account number, sort code, statement starting balance, statement finishing balance, 
statement period date, bank provider, total paid in, total withdrawn and the response should be of the following structure

 "Personal Information": {
    "Full Name": "John Testuser",
    "Address": "123 Test Lane, Testville, TX 00000",
    "Account Number": "11111111",
    "Sort Code": "00-00-00",
    "Statement Starting Balance": "£100.00",
    "Statement Finishing Balace": "£1,000.00",
    "Statement Period Date": "01 JAN 2023 to 31 JAN 2023",
    "Bank Provider": "Test Bank",
    "Total Paid In": "£3,250.00",
    "Total Withdrawn": "£250.75"
  },


"""