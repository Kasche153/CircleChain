import json
import base64
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, AssetFreezeTxn
from algosdk.future.transaction import *


# mnemonic1 = "december giggle gown trap bread soccer sort song judge island lift black bitter ghost impulse rice actress because ribbon unusual negative lucky monster above used"
# mnemonic2 = "welcome explain vast blind praise oak fire brush wreck jazz family sweet civil dynamic dance aim arrange bachelor flower earn brother pig giant absent digital"
# mnemonic3 = "amused burger uphold hurt stereo holiday summer inherit believe angry token pledge chicken blush repeat patrol common hungry hello hammer humor ski coach above flight"

# accounts = {}
# counter = 1
# for m in [mnemonic1, mnemonic2, mnemonic3]:
#     accounts[counter] = {}
#     accounts[counter]['pk'] = mnemonic.to_public_key(m)
#     accounts[counter]['sk'] = mnemonic.to_private_key(m)
#     counter += 1


# algod_address = "http://localhost:4001"
# algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
# algod_client = algod.AlgodClient(
#     algod_token=algod_token, algod_address=algod_address)


def create_asset(algod_client, creator_public_key, manager_public_key, creator_private_key):
    params = algod_client.suggested_params()

    txn = AssetConfigTxn(
        sender=creator_public_key,
        sp=params,
        total=1,
        default_frozen=False,
        unit_name="=3402",
        asset_name="Testing FILIP",
        manager=manager_public_key,
        reserve=manager_public_key,
        freeze=manager_public_key,
        clawback=manager_public_key,
        url="",
        decimals=0)

    # Sign with secret key of creator
    stxn = txn.sign(creator_private_key)

    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(
            confirmed_txn['confirmed-round']))

    except Exception as err:
        print(err)
    # Retrieve the asset ID of the newly created asset by first
    # ensuring that the creation transaction was confirmed,
    # then grabbing the asset id from the transaction.

    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))
    # print("Decoded note: {}".format(base64.b64decode(
    #     confirmed_txn["txn"]["txn"]["note"]).decode()))

    try:
        # Pull account info for the creator
        # account_info = algod_client.account_info(accounts[1]['pk'])
        # get asset_id from tx
        # Get the new asset's information from the creator account
        ptx = algod_client.pending_transaction_info(txid)
        asset_id = ptx["asset-index"]
        print_created_asset(algod_client, creator_public_key, asset_id)
        print_asset_holding(algod_client, creator_public_key, asset_id)
    except Exception as e:
        print(e)


def print_created_asset(algodclient, account, assetid):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then use 'account_info['created-assets'][0] to get info on the created asset
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info['created-assets']:
        scrutinized_asset = account_info['created-assets'][idx]
        idx = idx + 1
        if (scrutinized_asset['index'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['index']))
            print(json.dumps(my_account_info['params'], indent=4))
            break


def print_asset_holding(algodclient, account, assetid):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then loop thru the accounts returned and match the account you are looking for
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1
        if (scrutinized_asset['asset-id'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['asset-id']))
            print(json.dumps(scrutinized_asset, indent=4))
            break


asset_id = 81978905


def opt_in(algod_client, opt_in_account, opt_in_private_key):
    params = algod_client.suggested_params()

    account_info = algod_client.account_info(opt_in_account)
    holding = None
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1
        if (scrutinized_asset['asset-id'] == asset_id):
            holding = True
            break

    if not holding:

        # Use the AssetTransferTxn class to transfer assets and opt-in
        txn = AssetTransferTxn(
            sender=opt_in_account,
            sp=params,
            receiver=opt_in_account,
            amt=0,
            index=asset_id)
        stxn = txn.sign(opt_in_private_key)
        # Send the transaction to the network and retrieve the txid.
        try:
            txid = algod_client.send_transaction(stxn)
            print("Signed transaction with txID: {}".format(txid))
            # Wait for the transaction to be confirmed
            confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
            print("TXID: ", txid)
            print("Result confirmed in round: {}".format(
                confirmed_txn['confirmed-round']))

        except Exception as err:
            print(err)
        # Now check the asset holding for that account.
        # This should now show a holding with a balance of 0.
        print_asset_holding(algod_client, opt_in_account, asset_id)


create_asset()


def send(algod_client, asset_sender, asset_reciver, sender_private_key):
    params = algod_client.suggested_params()
    # comment these two lines if you want to use suggested params
    # params.fee = 1000
    # params.flat_fee = True
    txn = AssetTransferTxn(
        sender=asset_sender,
        sp=params,
        receiver=asset_reciver,
        amt=1,
        index=82829986)
    stxn = txn.sign(sender_private_key)
    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(
            confirmed_txn['confirmed-round']))

    except Exception as err:
        print(err)
    # The balance should now be 10.
    print_asset_holding(algod_client, asset_reciver, asset_id)
