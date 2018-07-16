"""
Basic settings for an NEP5 Token and crowdsale
"""
from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Storage import *
from boa.interop.Neo.Action import RegisterAction

TOKEN_NAME = 'The Senno Token'

TOKEN_SYMBOL = 'SENNO'

TOKEN_DECIMALS = 8

# This is the script hash of the address for the owner of the token
# This can be found in ``neo-python`` with the walet open, use ``wallet`` command
# TODO to be changed to the MainNet wallet address
TOKEN_OWNER = b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)'

TOKEN_CIRC_KEY = b'in_circulation'

TOKEN_TOTAL_SUPPLY = 10000000000 * 100000000  # 10b total supply * 10^8 ( decimals)

# TODO may need to be changed accordingly for presale
TOKEN_INITIAL_AMOUNT = 6000000000 * 100000000  # 6b initial tokens reserved to owners * 10^8

# One neo = 10k tokens * 10^8
TOKENS_PER_NEO = 10000 * 100000000

# One gas = 3.2k tokens * 10^8
TOKENS_PER_GAS = 3200 * 100000000

# maximum amount you can mint in the limited round ( 500 neo/person * 10k Tokens/NEO * 10^8 )
# TODO limited round
MAX_EXCHANGE_LIMITED_ROUND = 500 * 10000 * 100000000

# when to start the crowdsale
# TODO update the block height to 2483949 (need to calculate again)
BLOCK_SALE_START = 755000

# when to end the initial limited round
# TODO update the block height to 2483949 + 175316 (around 1 month)
LIMITED_ROUND_END = 755000 + 10000

KYC_KEY = b'kyc_ok'

LIMITED_ROUND_KEY = b'r1'

# TODO make sure the current bonus structure is correct
BOUNS = [
    [11520, 20], # 20% for the first 48hrs = 48 * 60 * 60 / 15
    [40320, 10], # 10% for the 1st week = 7 * 24 * 60 * 60 / 15
    [80640, 7], # 7% for the 2nd week = 14 * 24 * 60 * 60 / 15
    [120960, 3], # 3% for the 3rd week = 21 * 24 * 60 * 60 / 15
]

OnBurn = RegisterAction('burn', 'amount')

def crowdsale_available_amount(ctx):
    """

    :return: int The amount of tokens left for sale in the crowdsale
    """

    in_circ = Get(ctx, TOKEN_CIRC_KEY)

    available = TOKEN_TOTAL_SUPPLY - in_circ

    return available


def add_to_circulation(ctx, amount):
    """
    Adds an amount of token to circlulation

    :param amount: int the amount to add to circulation
    """

    current_supply = Get(ctx, TOKEN_CIRC_KEY)

    current_supply += amount
    Put(ctx, TOKEN_CIRC_KEY, current_supply)
    return True


def get_circulation(ctx):
    """
    Get the total amount of tokens in circulation

    :return:
        int: Total amount in circulation
    """
    return Get(ctx, TOKEN_CIRC_KEY)


def burn(ctx, args):
    """
    Burn unsold tokens, main use case is for crowdsale.

    :param amount: int the amount to be burned
    :return:
        int: Whether the tokens were successfully burned or not
    """
    amount = args[0]

    if CheckWitness(TOKEN_OWNER):
        current_in_circulation = Get(ctx, TOKEN_CIRC_KEY)
        new_amount = current_in_circulation + amount

        if amount <= 0:
            return False
        if new_amount > TOKEN_TOTAL_SUPPLY:
            return False

        current_balance = Get(ctx, 'BURNED_TOKENS')
        new_total = amount + current_balance
        Put(ctx, 'BURNED_TOKENS', new_total)

        # update the in circulation amount
        result = add_to_circulation(ctx, amount)

        # dispatch burn event
        OnBurn(amount)
        return True
    else:
        return False
