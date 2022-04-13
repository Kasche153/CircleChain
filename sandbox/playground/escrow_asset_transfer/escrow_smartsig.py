import base64
from http.client import OK

from algosdk.future import transaction
from algosdk import mnemonic
from algosdk.v2client import algod
from pyteal import *

# user declared account mnemonics
# Only the benefactor account can withdraw from escrow account
sender_mnemonic = "trust zoo tank romance staff quick search lonely drive neck light audit fringe rally width flock casino invite width odor gauge conduct dolphin absorb indoor"
benefactor_mnemonic = "bulk voyage divorce this poem slam check razor glass recycle round lottery force bomb dune metal raccoon cube much curtain borrow ancient mass ability stone"


# user declared algod connection parameters. Node must have EnableDeveloperAPI set to true in its config
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

# helper function to compile program source
def compile_smart_signature(client, source_code):
    compile_response = client.compile(source_code)
    return compile_response['result'], compile_response['hash']

# helper function that converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key

# This should become a Asset transfer to fund the smart_sig
def fund_escrow_txn(sender_mnemonic, amt, rcv, algod_client) -> dict:
    params = algod_client.suggested_params()
    add = mnemonic.to_public_key(sender_mnemonic)
    key = mnemonic.to_private_key(sender_mnemonic)
    unsigned_txn = transaction.PaymentTxn(add, params, rcv, amt)
    signed = unsigned_txn.sign(key)
    tx_id = algod_client.send_transaction(signed)
    
     # wait for confirmation
    try:
        pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(pmtx['confirmed-round']))

    except Exception as err:
        print(err)
        return
    return pmtx

# escrow address opting in before receiving asset
def escrow_account_opt_in(escrowProg, escrow_address, asset_id, algod_client):
    params = algod_client.suggested_params()
    unsigned_txn = transaction.AssetOptInTxn(escrow_address, params, asset_id)
    encodedProg = escrowProg.encode()
    program = base64.decodebytes(encodedProg)
    lsig = transaction.LogicSig(program)
    stxn = transaction.LogicSigTransaction(unsigned_txn, lsig)
    tx_id = algod_client.send_transaction(stxn)

     # wait for confirmation
    try:
        pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(pmtx['confirmed-round']))

    except Exception as err:
        print(err)
        return
    return pmtx

def regular_account_opt_in(rcv_mnemonic, asset_id, algod_client)->dict:
    params = algod_client.suggested_params()
    add = mnemonic.to_public_key(rcv_mnemonic)
    key = mnemonic.to_private_key(rcv_mnemonic)
    unsigned_txn = transaction.AssetOptInTxn(add, params, asset_id)
    signed = unsigned_txn.sign(key)
    tx_id = algod_client.send_transaction(signed)
    
    # wait for confirmation
    try:
        pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(pmtx['confirmed-round']))

    except Exception as err:
        print(err)
        return
    return pmtx


#
def to_escrow_asset_txn(sender_mnemonic, asset_id, rcv, algod_client)->dict:
    params = algod_client.suggested_params()
    add = mnemonic.to_public_key(sender_mnemonic)
    key = mnemonic.to_private_key(sender_mnemonic)
    unsigned_txn = transaction.AssetTransferTxn(add, params, rcv, 1, asset_id)
    signed = unsigned_txn.sign(key)
    tx_id = algod_client.send_transaction(signed)
    
    # wait for confirmation
    try:
        pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(pmtx['confirmed-round']))

    except Exception as err:
        print(err)
        return
    return pmtx


def lsig_asset_txn(escrowProg, escrow_address, asset_id, rcv, algod_client):
    params = algod_client.suggested_params()
    unsigned_txn = transaction.AssetTransferTxn(escrow_address, params, rcv, 1, asset_id)
    encodedProg = escrowProg.encode()
    program = base64.decodebytes(encodedProg)
    lsig = transaction.LogicSig(program)
    stxn = transaction.LogicSigTransaction(unsigned_txn, lsig)
    tx_id = algod_client.send_transaction(stxn)

     # wait for confirmation
    try:
        pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(pmtx['confirmed-round']))

    except Exception as err:
        print(err)
        return
    return pmtx


def donation_escrow(benefactor):
    Fee = Int(1000)

    # Only the benefactor account can withdraw from this escrow
    program = And(
        Txn.type_enum() == TxnType.AssetTransfer,
        Txn.fee() <= Fee,
        Txn.receiver() == Txn.asset_sender(),
        Global.group_size() == Int(1),
        Txn.rekey_to() == Global.zero_address()
    )

    # Mode.Signature specifies that this is a smart signature
    return compileTeal(program, Mode.Signature, version=5)


def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # define public keys
    sender_public_key = mnemonic.to_public_key(sender_mnemonic)
    benefactor_public_key = mnemonic.to_public_key(benefactor_mnemonic)

    stateless_program_teal = donation_escrow(benefactor_public_key)
    escrow_result, escrow_address = compile_smart_signature(
        algod_client, stateless_program_teal)

    print("--------------------------------------------")
    print("Escrow details:")
    print("Program:", escrow_result)
    print("hash: ", escrow_address)
    

    asset_id = 83658033


    """ Fund escrow to pay for tx fee (so escrow "afford" opting in) """
    print("--------------------------------------------")
    print("Funding escrow account")
    amt = 201000
    fund_escrow_txn(sender_mnemonic, amt, escrow_address, algod_client)

    
    """ Activate escrow contract by sending 1 ASA and 1000 microalgo for transaction fee from sender"""
    print("--------------------------------------------")
    print("Opting in escrow account")
    escrow_account_opt_in(escrow_result, escrow_address, asset_id, algod_client)


    """ Transfering asset from sender to escrow """
    print("--------------------------------------------")
    print("Sending asset to escrow")
    to_escrow_asset_txn(sender_mnemonic, asset_id, escrow_address, algod_client)


    """ Opting in receving account """
    print("--------------------------------------------")
    print("Opting in receiving account")
    regular_account_opt_in(benefactor_mnemonic, asset_id, algod_client)


    """ Benefactor withdrawing 1 ASA from smart signature using logic signature. """
    print("--------------------------------------------")
    print("Sending asset from escrow")
    lsig_asset_txn(escrow_result, escrow_address, asset_id, benefactor_public_key, algod_client)

main()