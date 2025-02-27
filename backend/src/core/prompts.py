"""
This file holds a set of reusable prompt strings for various AI assistants.
"""

GEMINI_STATEMENT_PARSE = """\
Please parse the attached financial statement PDF and a provide a csv response. Only return a valid .csv, no other text or comments, CSV output should have the following structure

For every single transaction identified, output the following data by parsing each line in the statement
Date of transaction,Description of transaction,Amount of transaction,Direction, either paid in  or withdrawn,Balance remaining, Category 

The category field must be present on every output line and must be assigned to one of the following categories by parsing the description data and inferring category

Category fields has to be one of the following an should be inferred from the transaction description:

1. Essential Home - Rent/Mortgage, monthly or weekly consistent payment - must be outgoing
2. Essential Household - Council Tax, Water, Electricity, Gas, Internet, TV Licence, Phone, Mobile, etc. - must be outgoing
3. Non-Essential Household - Sky TV, Netflix, Spotify, Disney+, Apple Music, cleaners, gardeners, etc. - must be outgoing
4. Salary - Money received from a salary or other regular payment - must be incoming
5. Non -Essential Entertainment - Going out, dining out, cinema, theatre, Uber, takeaways - must be outgoing
6. Gambling - Betting, Casino, Lotteries, etc. - Can be incoming or outgoing
7. Cash Withdrawal - Cash withdrawals from ATMs, banks, etc. - must be outgoing
8. Bank Transfer - Money transferred from one account to another - Can be outgoing or incoming
9. Unknown - Any other category that does not fit into the above


If the date is not clear parse the description data to infer.
Any dates must be output in the format dd-mm-yyyy 
There structure should be one transaction per row of CSV
Note that balance remaining may we be negative or overdrawn, possibly denoted with a minus sign or in brackets, or with an OD, or overdrawn. This must be represented in the banace reamining as a negative number


Note that no headers should be returned, just transaction data.
Provide exactly one row per transaction identified, do not skip any transactions for any reason, even missing or incomplete data

If the file does not seem to contain any transactions the just return an empty CSV
"""


GEMINI_PERSONAL_INFO_PARSE = """\

Please parse the attached financial statement PDF and a provide a csv response consisting of personal data only, 
ignore any transaction data. The data required is as follows 

full name, address, account number, sort code, statement starting balance, statement finishing balance, 
statement period date, bank provider, total paid in, total withdrawn.

Do not provide any other response, commentary or data, just the comma delimited fields highlighted above
"""

GEMINI_TRANSACTION_SUMMARY = """\
You are an expert at summarising financial transactions.
YOu are given a some personal information and a list of financial transactions and must provide a summary in a valid JSON format.
The incoming data follows the following format:

Date of transaction,Description of transaction,Amount of transaction,Direction, either paid in  or withdrawn,Balance remaining, Category 
 I would like you to summarise transaction, in and out, on a catergory by catergory basis and then give a general summary of the list of transactions from a financial health point of view. Are there any red flags in the list, anything to be concerns about?

You must parse the personal information from the data provided, provide a summary of total incoming and outgoing trasnactions at category level 
and then provide a general commentary on the transactions advising on general finanacial health, possible red flags or concerns, and any general reccomendations

The JSON needs to follow the following structure

{
  "personalInformation": {
    "name": "John Smith",
    "address": "123 Example Street, Example Town, EX1 1EX",
    "accountNumber": "12345678",
    "sortCode": "12-34-56",
    "statementStartingBalance": 8233.65,
    "statementFinishingBalance": 6174.17
  },
  "summaryOfIncomeAndOutgoings": {
    "income": {
      "Essential Home - Rent/Mortgage": 1250.00,
      "Essential Household": 145.99,
      "Unknown": 5275.00
    },
    "outgoings": {
      "Essential Household": 760.64,
      "Non-Essential Household": 33.00,
      "Essential Home - Rent/Mortgage": 0.00,
      "Unknown": 2898.84
    }
  },
  "generalSummaryAndFinancialHealthCommentary": {
    "overallBalance": "The account balance has decreased by £2059.48 during the statement period (from £8233.65 to £6174.17).",
    "inconsistentCategorization": "There are a lot of transactions labelled as 'Unknown.' More specific categorization is needed for proper budgeting and analysis.",
    "essentialHouseholdSpending": "A significant amount is spent on essential household bills.",
    "transfers": "Frequent transfers to and from 'BYRON C' and 'BYRON CJ' suggest money moving between accounts without clear purposes.",
    "standingOrdersAndDirectDebits": "Several standing orders and direct debits are active.",
    "paymentsToIndividuals": "Numerous small payments to individuals could indicate informal lending or reimbursements.",
    "rentMortgagePayments": "Rent/Mortgage payments are made regularly.",
    "councilTaxPayments": "Council tax is being paid on a regular basis.",
    "incomeNote": "It's unclear what the main source of income is; some rent payments may not be 'income' in the strict sense."
  },
  "potentialRedFlagsAndConcerns": [
    "High 'Unknown' Category Spending: Indicates lack of tracking and control over finances.",
    "Frequent Small Transfers: Could be a sign of poor budgeting or overspending without clarity.",
    "Decreasing Balance: Balance declined over the period, unclear if temporary or long-term.",
    "Dependence on Transfers: A large portion of income comes from transfers, suggesting reliance on them."
  ],
  "recommendations": [
    "Categorize Transactions: Categorize all 'Unknown' items to see where money is truly going.",
    "Budgeting: Create a detailed budget to manage income and expenses.",
    "Investigate Transfers: Understand the purpose of frequent transfers to 'BYRON C' and 'BYRON CJ'.",
    "Review Direct Debits and Standing Orders: Ensure they are necessary and amounts are correct.",
    "Seek Financial Advice: If the balance keeps declining or financial management is challenging, consult a professional."
  ]
}
"""