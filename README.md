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

An expense is associated with its user through a foreign key relationship.