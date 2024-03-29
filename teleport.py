from ontology.builtins import *

from ontology.interop.System.Blockchain import GetHeight, GetHeader, GetBlock
from ontology.interop.System.Transaction import GetTransactionHash
from ontology.interop.System.Header import GetBlockHash
from ontology.interop.System.ExecutionEngine import *
from ontology.interop.System.Runtime import *
from ontology.interop.System.Storage import GetContext, Get, Put, Delete
from ontology.interop.System.Runtime import Notify, CheckWitness
from ontology.interop.System.Action import RegisterAction
from ontology.interop.Ontology.Native import Invoke
from ontology.builtins import concat
from ontology.interop.Ontology.Runtime import Base58ToAddress
# from boa.interop.Ontology.Runtime import AddressToBase58, Base58ToAddress

TransferEvent = RegisterAction("transfer", "from", "to", "amount")
ApprovalEvent = RegisterAction("approval", "owner", "spender", "amount")

ctx = GetContext()
ctx2={}
NAME = 'MyToken'
SYMBOL = 'MYT'
DECIMALS = 8
FACTOR = 100000000
OWNER = Base58ToAddress("ANjLLTmEysG3uHorMJndWKumhfDfMNe5hi")
#ONGAddress = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02')
# OWNER = bytearray(b'\x61\x6f\x2a\x4a\x38\x39\x6f\xf2\x03\xea\x01\xe6\xc0\x70\xae\x42\x1b\xb8\xce\x2d')
TOTAL_AMOUNT = 1000000000
BALANCE_PREFIX = bytearray(b'\x01')
APPROVE_PREFIX = b'\x02'
SUPPLY_KEY = 'TotalSupply'


def Main(operation, args):
    """
    :param operation:
    :param args:
    :return:
    """
    # 'init' has to be invokded first after deploying the contract to store the necessary and important info in the blockchain
    if operation == 'init':
        return init()
    if operation == 'name':
        return name()
    if operation == 'symbol':
        return symbol()
    if operation == 'decimals':
        return decimals()
    if operation == 'totalSupply':
        return totalSupply()
    if operation == 'balanceOf':
        if len(args) != 1:
            return False
        acct = args[0]
        return balanceOf(acct)
    if operation == 'transfer':
        if len(args) != 3:
            return False
        else:
            from_acct = args[0]
            to_acct = args[1]
            amount = args[2]
            return transfer(from_acct, to_acct, amount)
    if operation == 'transferMulti':
        return transferMulti(args)
    if operation == 'transferFrom':
        if len(args) != 4:
            return False
        spender = args[0]
        from_acct = args[1]
        to_acct = args[2]
        amount = args[3]
        return transferFrom(spender, from_acct, to_acct, amount)
    if operation == 'approve':
        if len(args) != 3:
            return False
        owner = args[0]
        spender = args[1]
        amount = args[2]
        return approve(owner, spender, amount)
    if operation == 'allowance':
        if len(args) != 2:
            return False
        owner = args[0]
        spender = args[1]
        return allowance(owner, spender)
    if operation=='registeringOrder':
        if len(args)!=6:
            return False
        order_account=args[0]
        biddingTime=args[1]
        radius=args[2]
        weight=args[3]
        pickupLocation=args[4]
        destination=args[5]
        
        return registeringOrder(order_account, biddingTime, radius, weight, pickupLocation, destination)
    if operation=='acceptBidding':
        if len(args)!=4:
            return False
        txHash=args[0]
        bidder_account=args[1]
        biddingAmount=args[2]
        deliveryTime=args[3]
        return acceptBidding(txHash, bidder_account, biddingAmount, deliveryTime)
    if operation=='deleteOrder':
        if len(args)!=2:
            return False
        txHash=args[0]
        order_account=args[1]
        return deleteOrder(txHash, order_account)
    if operation=='deleteMyBid':
        if len(args)!=2:
            return False
        bidder_account=args[0]
        txHash=args[1]
        return deleteMyBid(bidder_account,txHash)
    if operation=='modifyOrder':
        if len(args)!=7:
            return False
        txHash=args[0]
        order_account=args[1]
        biddingTime=args[2]
        radius=args[3]
        weight=args[4]
        pickupLocation=args[5]
        destination=args[6]
        return modifyOrder(txHash, order_account, biddingTime, radius, weight, pickupLocation, destination)
    return False
    

def init():
    """
    initialize the contract, put some important info into the storage in the blockchain
    :return:
    """
    if len(OWNER) != 20:
        Notify(["Owner illegal!"])
        return False
    if Get(ctx, SUPPLY_KEY):
        Notify("Already initialized!")
        return False
    else:
        total = TOTAL_AMOUNT * FACTOR
        Put(ctx, SUPPLY_KEY, total)
        Put(ctx, concat(BALANCE_PREFIX, OWNER), total)

        # Notify(["transfer", "", Base58ToAddress(OWNER), total])
        # ownerBase58 = AddressToBase58(OWNER)
        TransferEvent("", OWNER, total)

        return True


def name():
    """
    :return: name of the token
    """
    return NAME


def symbol():
    """
    :return: symbol of the token
    """
    return SYMBOL


def decimals():
    """
    :return: the decimals of the token
    """
    return DECIMALS


def totalSupply():
    """
    :return: the total supply of the token
    """
    return Get(ctx, SUPPLY_KEY)


def balanceOf(account):
    """
    :param account:
    :return: the token balance of account
    """
    if len(account) != 20:
        raise Exception("Address length error")
    return Get(ctx, concat(BALANCE_PREFIX, account))


def transfer(from_acct, to_acct, amount):
    """
    Transfer amount of tokens from from_acct to to_acct
    :param from_acct: the account from which the amount of tokens will be transferred
    :param to_acct: the account to which the amount of tokens will be transferred
    :param amount: the amount of the tokens to be transferred, >= 0
    :return: True means success, False or raising exception means failure.
    """
    if len(to_acct) != 20 or len(from_acct) != 20:
        raise Exception("Address length error")
    if CheckWitness(from_acct) == False:
        return False

    fromKey = concat(BALANCE_PREFIX, from_acct)
    fromBalance = Get(ctx, fromKey)
    if amount > fromBalance:
        return False
    if amount == fromBalance:
        Delete(ctx, fromKey)
    else:
        Put(ctx, fromKey, fromBalance - amount)

    toKey = concat(BALANCE_PREFIX, to_acct)
    toBalance = Get(ctx, toKey)
    Put(ctx, toKey, toBalance + amount)

    #Use VaasAssert here to determine if the logic is correct
    VaasAssert(fromBalance > Get(ctx, fromKey))
    TransferEvent(from_acct, to_acct, amount)


def transferMulti(args):
    """
    :param args: the parameter is an array, containing element like [from, to, amount]
    :return: True means success, False or raising exception means failure.
    """
    for p in args:
        if len(p) != 3:
            # return False is wrong
            raise Exception("transferMulti params error.")
        VaasRequire(transfer(p[0], p[1], p[2]))
    return True


def approve(owner, spender, amount):
    """
    owner allow spender to spend amount of token from owner account
    Note here, the amount should be less than the balance of owner right now.
    :param owner:
    :param spender:
    :param amount: amount>=0
    :return: True means success, False or raising exception means failure.
    """
    if len(spender) != 20 or len(owner) != 20:
        raise Exception("Address length error")
    if CheckWitness(owner) == False:
        return False
    if amount > balanceOf(owner):
        return False

    key = concat(concat(APPROVE_PREFIX, owner), spender)
    Put(ctx, key, amount)

    # Notify(["approval", AddressToBase58(owner), AddressToBase58(spender), amount])
    # ApprovalEvent(AddressToBase58(owner), AddressToBase58(spender), amount)
    ApprovalEvent(owner, spender, amount)

    return True


def transferFrom(spender, from_acct, to_acct, amount):
    """
    spender spends amount of tokens on the behalf of from_acct, spender makes a transaction of amount of tokens
    from from_acct to to_acct
    :param spender:
    :param from_acct:
    :param to_acct:
    :param amount:
    :return:
    """
    if len(spender) != 20 or len(from_acct) != 20 or len(to_acct) != 20:
        raise Exception("Address length error")
    if CheckWitness(spender) == False:
        return False

    fromKey = concat(BALANCE_PREFIX, from_acct)
    fromBalance = Get(ctx, fromKey)
    if amount > fromBalance:
        return False

    approveKey = concat(concat(APPROVE_PREFIX, from_acct), spender)
    approvedAmount = Get(ctx, approveKey)
    toKey = concat(BALANCE_PREFIX, to_acct)
    toBalance = Get(ctx, toKey)
    if amount > approvedAmount:
        return False
    elif amount == approvedAmount:
        Delete(ctx, approveKey)
        Put(ctx, fromKey, fromBalance - amount)
    else:
        Put(ctx, approveKey, approvedAmount - amount)
        Put(ctx, fromKey, fromBalance - amount)
        VaasAssert(approvedAmount > Get(ctx, approveKey))

    Put(ctx, toKey, toBalance + amount)
    VaasAssert(toBalance < Get(ctx, toKey))
    VaasAssert(fromBalance > Get(ctx, fromKey))
    #TransferEvent(from_acct, to_acct, amount)

    return True


def allowance(owner, spender):
    """
    check how many token the spender is allowed to spend from owner account
    :param owner: token owner
    :param spender:  token spender
    :return: the allowed amount of tokens
    """
    key = concat(concat(APPROVE_PREFIX, owner), spender)
    return Get(ctx, key)


def Revert():
    """
    Revert the transaction. The opcodes of this function is `09f7f6f5f4f3f2f1f000f0`,
    but it will be changed to `ffffffffffffffffffffff` since opcode THROW doesn't
    work, so, revert by calling unused opcode.
    """
    raise Exception(0xF1F1F2F2F3F3F4F4)


"""
https://github.com/ONT-Avocados/python-template/blob/master/libs/SafeCheck.py
"""




def VaasAssert(expr):
    if not expr:
        raise Exception("AssertError")

def VaasRequire(expr):
    if not expr:
        raise Exception("RequireError")
def concatkey(str1,str2):
    return concat(concat(str1, '_'), str2)
        
def registeringOrder(order_account, biddingTime, radius, weight, pickupLocation, destination):
    RequireIsAddress(order_account)
    RequireWitness(order_account)
        
    orderTime=GetTime()
    ctx3={}
    txHash = GetTransactionHash(GetScriptContainer())
    #entry=GetEntryScriptHash()
    #calling=GetCallingScriptHash()
    #exect=GetExecutingScriptHash()
    ctx3["biddingTime"]=biddingTime
    ctx3["radius"]=radius
    ctx3["weight"]=weight
    ctx3["pickupLocation"]=pickupLocation
    ctx3["destination"]=destination
    ctx3["orderTime"]=orderTime
    ctx3["txHash"]=txHash
    ctx3["order_account"]=order_account
    Log('registered')
    #Log(txHash)
    Put(ctx, txHash, Serialize(ctx3))
        
    #Notify(entry)
    #Notify(calling)
    #Notify(exect)
    #Notify(orderTime)
    return True
def ds(dic):
    ss=Deserialize(Get(ctx, dic))
    Put(ctx, "dict", Serialize(ss))
    ans=Deserialize(Get(ctx,"dict"))
    Delete(ctx,"dict")
    return ans



def acceptBidding(txHash, bidder_account, biddingAmount, deliveryTime):
    RequireIsAddress(bidder_account)
    RequireWitness(bidder_account)
    if GetEntryScriptHash()==GetCallingScriptHash():
        ctx3=ds(txHash)
        Notify(ctx3["txHash"])
        if txHash==ctx3["txHash"]:
            orderTime=ctx3["orderTime"]
            timeDiff=GetTime()-orderTime
            biddingTime=ctx3["biddingTime"]
            if timeDiff<biddingTime:
                ctx2['biddingAmount']=biddingAmount
                ctx2['deliveryTime']=deliveryTime
                ctx2['bidder_account']=bidder_account
                ctx3[bidder_account]=ctx2
                Put(ctx, txHash, Serialize(ctx3))
                return True
                
            
        
        #AZ5JJ5RdVopJZ2JL9Qyemkn4sErSyXvUmo
                    
    
def deleteOrder(txHash,order_account):
    RequireIsAddress(order_account)
    RequireWitness(order_account)
    if GetEntryScriptHash()==GetCallingScriptHash():
        ctx3=ds(txHash)
        if order_account==ctx3["order_account"]:
            Delete(ctx,txHash)
            return True
        else:
            Log("I'm afraid! This is not your order!")
            return False
    else:
        Log("Get Lost!")
        return False
def deleteMyBid(bidder_account,txHash):
    RequireIsAddress(bidder_account)
    RequireWitness(bidder_account)
    if GetEntryScriptHash()==GetCallingScriptHash():
        ctx3=ds(txHash)
        #ctx2=ctx3[bidder_account]
        #Notify(ctx2)
        if bidder_account==ctx3[bidder_account]['bidder_account']:
            ctx3[bidder_account]=None
            Put(ctx,txHash,Serialize(ctx3))
            return True
        else:
            Log("I'm afraid! This is not your bid!")
            return False
    else:
        Log("Get Lost!")
        return False
def modifyOrder(txHash, order_account, biddingTime, radius, weight, pickupLocation, destination):
    RequireIsAddress(order_account)
    RequireWitness(order_account)
    if GetEntryScriptHash()==GetCallingScriptHash():
        ctx3=ds(txHash)
        if order_account==ctx3["order_account"]:
            ctx3["biddingTime"]=biddingTime
            ctx3["radius"]=radius
            ctx3["weight"]=weight
            ctx3["pickupLocation"]=pickupLocation
            ctx3["destination"]=destination
            ctx3["txHash"]=txHash
            Put(ctx, txHash, Serialize(ctx3))
            Log('modified')
            return True
        else:
            Log("I'm afraid! This is not your order!")
            return False
    else:
        Log("Get Lost!")
        return False
    #require 
    
def RequireIsAddress(address):
    Require(len(address) == 20, 'Address has invalid length')
def RequireWitness(address):
    Require(CheckWitness(address), 'Address is not witness')
def Require(expr, message='There was an error'):
    if not expr:
        Log(message)
        raise Exception(message)

