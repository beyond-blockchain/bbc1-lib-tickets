Library for General Ticket Management
===========================================
## Set of functionality for ticket management
### ticket_lib.py
**ticket_lib.py** contains **ticket** and **ticket service** classes to deal with creation, transfer and redemption of tickets. A ticket can include an arbitrary data structure, value in a specified unit, time to begin and end, and when to expire. A book of tickets can also be handled. A ticket may be divisible, and/or transferable.

The following methods are provided:
* **get_balance_of()** to get (estimated) ticket values owned by a user at a given time.
* **get_total_supply()** to get the total (estimated) ticket values at the service at a given time.
* **is_valid()** to see whether the ticket is valid or not.
* **is_valid_holder()** to see whether the specified user is the valid holder of the ticket.
* **issue()** to issue a ticket to a user.
* **redeem()** to redeem a ticket for a user.
* **split()** to split a ticket into divisions.
* **swap()** to swap tickets between users.
* **transfer()** to transfer a ticket from a user to another user.

## How to Use this library
Coming soon.
