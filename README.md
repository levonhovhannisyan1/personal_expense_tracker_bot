# personal_expense_tracker_bot

A Telegram bot for managing and tracking personal and family expenses directly from Telegram.


## Version

**v0.1.0**


## Features

### User Management
- Telegram user registration
- User names associated with Telegram accounts
- Support for multiple users
- Family expense visibility
- Each user can see their own expenses
- Shared family expenses can be viewed according to the configured access rules

### Expense Management
- Add expenses
- Edit existing expenses
- Delete expenses
- View individual expenses
- View a list of expenses
- View current and next month expense totals
- Expense categories
- Expense descriptions
- Expense amounts in AMD
- Expense month
- Expense creation date and time

### Expense Categories
The bot currently supports expense categories including:

- Food
- Transport
- Shopping
- Bills
- Entertainment
- Health
- Sport
- Other

### Monthly Expense Planning
Expenses can be assigned to a specific month.

The selected month is displayed together with the expense, allowing expenses to be planned and organized by month.

### Income and Savings

On the 2nd day of every month at 10:00 Asia/Yerevan time, the bot sends the owner a pinned overall summary for the previous month, saves compact balance snapshots, archives that month's detailed records, then asks the owner to enter income for the current month. Income entries are additive, so secondary income can be added through the main menu.

Statistics show monthly income, expenses, and savings. Savings are calculated as income minus expenses.

Each user can set a starting savings balance once from the main menu. Statistics then show the running total balance: starting savings plus all tracked monthly savings. Compact monthly snapshots preserve that balance after detailed records are archived.

### Telegram Interface
The bot uses Telegram inline keyboards for navigation and actions.

The general flow is designed so that:

- Actions are performed inside a single interaction flow
- Temporary input messages can be removed after processing
- Action results are displayed after an operation
- The main menu is shown after completing an action
- Expense windows can be deleted when navigating back
- Edit and cancel operations clean up their previous windows
- Invalid input produces an appropriate error message

### Expense Editing
Existing expenses can be edited using the same interaction pattern as adding an expense.

When editing an expense, its current values are displayed first:

- Category
- Amount
- Description
- Month

The user can then change the required fields and save the updated expense.

### Database
The project uses SQLAlchemy as the ORM.

Current database entities include:

- `User`
- `Expense`
- `Income`

Expenses and income records are associated with their user through foreign key relationships.

## Setup
1. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`, then replace the placeholder token, Telegram IDs, and names.

3. Start the bot:

   ```bash
   python3 -m bot.main
   ```

Only the configured owner and family member can use the bot. The owner can view, edit, and delete all registered expenses; the other configured user can manage only their own.

The bot must be running on the 2nd at 10:00 Asia/Yerevan time to send the monthly income reminder. The owner must first open a private chat with the bot and send `/start`, otherwise Telegram will not allow the bot to message them.