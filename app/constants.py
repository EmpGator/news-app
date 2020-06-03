from enum import Enum
import os

"""
Contains constant parameters for app
"""


FINNPLUS_DOMAIN = os.environ.get('FINNPLUS_DOMAIN')
# in future this should be list of domains
PUBLISHER_DOMAIN = os.environ.get('PUBLISHER_DOMAIN')

# amount of days subscription lasts
SUBS_TIME = 30
# Amount of articles you can access with package
BUNDLE_SIZE = 15

# spl address where tokens paid goes
SLP_ADDR = 'simpleledger:qq0nu0xa5rxj72wx043ulhm3qs28y95davd6djawyh'
# token prices for different payments
MONTH_PRICE = 950
BUNDLE_PRICE = 645
SINGLE_PRICE = 50
BAD_CHAR_LIST = list('!"@#£¤$%&/{([)]=}+?\\´`\'<>|¨^~*,.-_;:½§1234567890')


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
    NON = "-1"
    NULL = ""
    MONTHLY = "0"
    PACKAGE = "1"
    SINGLE = "2"

class Category(Enum):
    POLITICS = 'politics'
    SPORTS  = 'sports'
    ECONOMY = 'economy'
    TECHNOLOGY = 'technology'
    HEALTH = 'health'
    ENTERTAINMENT = 'entertainment'
    OTHER = ''

    def __str__(self):
        return self.name


class Device(Enum):
    PC = "pc"
    TABLET = "tablet"
    MOBILE = "mobile"
    UNKNOWN = ""

