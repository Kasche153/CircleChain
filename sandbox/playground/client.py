import re
import os
from algosdk.v2client import algod
from algosdk import account, mnemonic, constants
from algosdk.future import transaction
import json
import base64


my_address = os.getenv("my_address")
txn_recipient = os.getenv("txn_recipient")
private_key = os.getenv("private_key")
amount = 100005


def init_client():
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    return algod_client


def fetch_balance(algod_client):
    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos".format(
        account_info.get('amount')) + "\n")


def build_params(algod_client):
    params = algod_client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = constants.MIN_TXN_FEE
    return params


def build_txn(algod_client, params):
    note = "Hello World".encode()
    unsigned_txn = transaction.PaymentTxn(
        my_address, params, txn_recipient, amount, None, note)
    return unsigned_txn


def sign_txn(unsigned_txn):
    # sign transaction
    signed_txn = unsigned_txn.sign(private_key)
    return signed_txn


def submit_txn(signed_txn, algod_client, params):
    # submit transaction
    txid = algod_client.send_transaction(signed_txn)
    print("Successfully sent transaction with txID: {}".format(txid))

    # wait for confirmation
    try:
        confirmed_txn = transaction.wait_for_confirmation(
            algod_client, txid, 4)
    except Exception as err:
        print(err)
        return

    account_info = algod_client.account_info(my_address)
    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))
    print("Decoded note: {}".format(base64.b64decode(
        confirmed_txn["txn"]["txn"]["note"]).decode()))
    print("Starting Account balance: {} microAlgos".format(
        account_info.get('amount')))
    print("Amount transfered: {} microAlgos".format(amount))
    print("Fee: {} microAlgos".format(params.fee))
    print("Final Account balance: {} microAlgos".format(
        account_info.get('amount')) + "\n")
    return confirmed_txn


def first_transaction_example(private_key, my_address):
    algod_client = init_client()
    fetch_balance(algod_client)
    params = build_params(algod_client)
    unsigned_txn = build_txn(algod_client, params)
    signed_txn = sign_txn(unsigned_txn)
    confirmed_txn = submit_txn(signed_txn, algod_client, params=params)


first_transaction_example(private_key=private_key, my_address=my_address)
