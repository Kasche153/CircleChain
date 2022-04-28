import json
import base64
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, AssetFreezeTxn
from algosdk.future.transaction import *


# Shown for demonstration purposes. NEVER reveal secret mnemonics in practice.
# Change these values with your mnemonics
mnemonic1 = "bulk voyage divorce this poem slam check razor glass recycle round lottery force bomb dune metal raccoon cube much curtain borrow ancient mass ability stone"
mnemonic2 = "bulk voyage divorce this poem slam check razor glass recycle round lottery force bomb dune metal raccoon cube much curtain borrow ancient mass ability stone"
mnemonic3 = "smile often modify quick horror type route garbage square kiwi release flame village heavy much drill alone glimpse client bench orange lend ahead absent glow"
# never use mnemonics in production code, replace for demo purposes only

# For ease of reference, add account public and private keys to
# an accounts dict.
accounts = {}
counter = 1
for m in [mnemonic1, mnemonic2, mnemonic3]:
    accounts[counter] = {}
    accounts[counter]['pk'] = mnemonic.to_public_key(m)
    accounts[counter]['sk'] = mnemonic.to_private_key(m)
    counter += 1

# Specify your node address and token. This must be updated.
# algod_address = ""  # ADD ADDRESS
# algod_token = ""  # ADD TOKEN

algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

# Initialize an algod client
algod_client = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address)


#   Utility function used to print created asset for account and assetid
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

#   Utility function used to print asset holding for account and assetid
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

print("Account 1 address: {}".format(accounts[1]['pk']))
print("Account 2 address: {}".format(accounts[2]['pk']))
print("Account 3 address: {}".format(accounts[3]['pk']))

asset_id = 83301516


# DESTROY ASSET
# With all assets back in the creator's account,
# the manager (Account 1) destroys the asset.
params = algod_client.suggested_params()
# comment these two lines if you want to use suggested params
# params.fee = 1000
# params.flat_fee = True

# Asset destroy transaction
txn = AssetConfigTxn(
    sender=accounts[1]['pk'],
    sp=params,
    index=asset_id,
    strict_empty_address_check=False
    )

# Sign with secret key of creator
stxn = txn.sign(accounts[1]['sk'])
# Send the transaction to the network and retrieve the txid.
# Send the transaction to the network and retrieve the txid.
try:
    txid = algod_client.send_transaction(stxn)
    print("Signed transaction with txID: {}".format(txid))
    # Wait for the transaction to be confirmed
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
    print("TXID: ", txid)
    print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))     
except Exception as err:
    print(err)

# Asset was deleted.
try:
    print("Account 3 must do a transaction for an amount of 0, " )
    print("with a close_assets_to to the creator account, to clear it from its accountholdings")
    print("For Account 1, nothing should print after this as the asset is destroyed on the creator account")
   
    print_asset_holding(algod_client, accounts[1]['pk'], asset_id)
    print_created_asset(algod_client, accounts[1]['pk'], asset_id)
    # asset_info = algod_client.asset_info(asset_id)
except Exception as e:
    print(e)