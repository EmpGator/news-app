from enum import Enum

"""
Contains constant parameters for app
"""

# in future this should be list of domains
PUBLISHER_DOMAIN = 'tridample.eu.pythonanywhere.com'

# amount of days subscription lasts
SUBS_TIME = 30
# Amount of articles you can access with package
BUNDLE_SIZE = 15

# spl address where tokens paid goes
SLP_ADDR = 'simpleledger:qq0nu0xa5rxj72wx043ulhm3qs28y95davd6djawyh'
# token prices for different payments
MONTH_PRICE = 1000
BUNDLE_PRICE = 500
SINGLE_PRICE = 100

class Role(Enum):
    """
    Enumeration for User roles.

    Valid options are:

    USER

    PUBLISHER

    ADMIN
    """
    USER = 'user'
    PUBLISHER = 'publisher'
    ADMIN = 'admin'

class PayOptions(Enum):
    """
    Enumeration for payment options

    Valid options are:

    NULL

    MONTHLY

    PACKAGE

    SINGLE

    """
    NULL = "0"
    MONTHLY = "1"
    PACKAGE = "2"
    SINGLE = "3"