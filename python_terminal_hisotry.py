# Code for printing the entire history:
# Python 3

# One-liner (quick copy and paste):

import readline; print('\n'.join([str(readline.get_history_item(i + 1)) for i in range(readline.get_current_history_length())]))

# (Or longer version...)

import readline
for i in range(readline.get_current_history_length()):
    print (readline.get_history_item(i + 1))

# Python 2

# One-liner (quick copy and paste):

import readline; print '\n'.join([str(readline.get_history_item(i + 1)) for i in range(readline.get_current_history_length())])
