# personal_expense_tracker_bot

A Telegram bot for managing personal and family finances directly from Telegram.

The bot is designed for a small family setup where multiple users can manage their own expenses while sharing overall financial statistics.

## Version
**v1.0.0**

## Features
### User Management
* Telegram user registration
* User names associated with Telegram accounts
* Support for multiple configured users
* Role-based access between the owner and secondary users
* Private expense data for each user
* Overall financial statistics shared between configured users

### Expense Management
* Add expenses
* Edit existing expenses
* Delete expenses
* View individual expenses
* View a list of personal expenses
* View current and next month expense totals
* Expense categories
* Expense descriptions
* Expense amounts in AMD
* Assign expenses to a specific month
* Store expense creation date and time

### Expense Categories
The bot currently supports the following categories:

* Food
* Transport
* Shopping
* Bills
* Entertainment
* Health
* Sport
* Other

### Monthly Expense Planning
Expenses can be assigned to a specific month instead of being limited to the month in which they are entered.

The selected month is displayed with the expense, making it possible to plan and organize expenses for the current or upcoming month.

### Income Management
The owner can add monthly income through the Telegram interface.

* Add income for the current month
* Add additional income during the month
* Income is accumulated rather than replacing previously recorded income
* Income is included in monthly statistics and savings calculations

The secondary user cannot add income.

### Savings and Balance Management
The owner can set the starting balance once.

The starting balance represents the amount of money available before tracked monthly financial activity.

After the starting balance has been set, the owner can use **Adjust balance** to correct the running balance without overwriting the original starting balance.

For example, if the bot records 5,000 AMD of expenses but the actual amount spent was 4,000 AMD, the owner can make a **+1,000 AMD** balance adjustment.

Balance adjustments can be positive or negative:

* Positive adjustment → increases the balance
* Negative adjustment → decreases the balance

The secondary user cannot set or adjust the balance.

### Statistics
The statistics section provides an overall view of the family's financial activity.

Statistics include:

* Monthly income
* Monthly expenses
* Monthly savings
* Current balance
* Previous/current monthly financial information
* Combined statistics for all configured users

The secondary user cannot see the owner's individual expense records, but can see the overall family statistics.

Savings are calculated as:

**Savings = Income − Expenses**

The running balance is calculated from the starting balance, monthly savings, and balance adjustments.

### Monthly Financial Processing
On the **2nd day of every month at 10:00 Asia/Yerevan time**, the bot performs the monthly financial processing.

The process:

1. Generates an overall summary for the previous month.
2. Sends the summary to the owner.
3. Pins the summary message in the owner's chat.
4. Saves a compact monthly financial snapshot.
5. Archives the previous month's financial information.
6. Removes the archived detailed expense and income records from the active database.
7. Sends the owner a reminder to enter the new month's income.

Monthly summaries preserve historical financial information after detailed expense and income records have been removed.

The scheduled process requires the bot to be running at the scheduled time.

### Telegram Interface
The bot uses Telegram inline keyboards for navigation and actions.

The interface is designed so that:

* Actions are performed through interactive buttons and messages
* Temporary input messages can be removed after processing
* Action results are displayed after an operation
* The main menu is shown after completing an action
* Expense windows can be removed when navigating back
* Edit and cancel operations clean up their previous messages
* Invalid input produces an appropriate error message
* Owner-only actions are hidden from the secondary user
* Users only see actions available to their role

### Expense Editing
Existing expenses can be edited using the same interactive pattern as adding an expense.

When editing an expense, its current values are displayed first:

* Category
* Amount
* Description
* Month

The user can then modify the required fields and save the updated expense.

### Access Control
The bot has two configured user roles.
#### Owner
The owner can:

* Add expenses
* Edit expenses
* Delete expenses
* View all registered expenses
* Add income
* Set the starting balance
* Adjust the balance
* View overall family statistics

#### Secondary User
The secondary user can:

* Add their own expenses
* Edit their own expenses
* Delete their own expenses
* View their own expenses
* View overall family statistics

The secondary user cannot:

* View the owner's individual expenses
* Add income
* Set the starting balance
* Adjust the balance

### Database
The project uses **SQLAlchemy** as its ORM.

The database contains entities for:

* `User`
* `Expense`
* `Income`
* `SavingsSetting`
* `BalanceAdjustment`
* `MonthlySummary`

Expenses, income, and balance information are associated with users through database relationships and foreign keys.

`MonthlySummary` stores compact historical financial information so that monthly statistics can remain available after detailed expense and income records are archived.

### Project Structure
The project is organized into separate modules for:

* Database models and connection
* Telegram handlers
* Keyboards
* Business logic and services
* Authorization
* Configuration
* Telegram utilities

This separation keeps Telegram interaction logic independent from database and financial calculation logic.

## Setup
### 1. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then configure the required Telegram bot token, Telegram user IDs, and user names.

### 4. Start the bot
```bash
python3 -m bot.main
```

## Access
Only the configured users can access the bot.

The owner has full financial-management access, while the secondary user can manage only their own expenses and view shared financial statistics.

The owner must first open a private chat with the bot and send `/start`. This is required because Telegram does not allow a bot to initiate a private conversation with a user who has not previously interacted with it.

## Monthly Reminder Requirement
The bot's monthly processing is scheduled for:

**Day:** 2nd of every month
**Time:** 10:00
**Timezone:** Asia/Yerevan

The bot must be running at the scheduled time for the monthly processing and income reminder to execute.