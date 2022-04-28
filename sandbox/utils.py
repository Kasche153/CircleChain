import base64
import json
from algosdk.future import transaction
from algosdk.future.transaction import PaymentTxn, AssetConfigTxn, AssetTransferTxn
from algosdk import mnemonic, account


# UTIL FUNCTIONS for creating accounts, transaction, payments, etc


def generate_algorand_keypair():
    private_key, address = account.generate_account()
    print("My address: {}".format(address))
    print("My private key: {}".format(private_key))
    print("My passphrase: {}".format(mnemonic.from_private_key(private_key)))

# FUNDING OF ACCOUNTS IS ALSO POSSIBLE WITH THE TEST_NET_FAUCET


def algo_transaction(add, key, amount, reciver, algod_client) -> dict:

    params = algod_client.suggested_params()
    unsigned_txn = PaymentTxn(
        add, params, reciver, amount)
    signed = unsigned_txn.sign(key)
    tx_id = algod_client.send_transaction(signed)
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
    return pmtx


def compile_smart_signature(client, source_code):
    compile_response = client.compile(source_code)
    return compile_response['result'], compile_response['hash']


def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])


def deploy_new_application(algod_client, creator_private_key, compiled_teal, compiled_clear_teal):

    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 0
    global_ints = 1
    global_bytes = 0
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    # compile program to TEAL assembly
    with open("./approval.teal", "w") as f:
        approval_program_teal = compiled_teal()
        f.write(approval_program_teal)

    # compile program to TEAL assembly
    with open("./clear.teal", "w") as f:
        clear_state_program_teal = compiled_clear_teal()
        f.write(clear_state_program_teal)

    # compile program to binary
    approval_program_compiled = compile_program(
        algod_client, approval_program_teal)

    # compile program to binary
    clear_state_program_compiled = compile_program(
        algod_client, clear_state_program_teal)

    print("--------------------------------------------")
    print("Deploying application......")

    # create new application on the blockchain
    app_id = create_app(algod_client, creator_private_key, approval_program_compiled,
                        clear_state_program_compiled, global_schema, local_schema)

    return app_id


def create_app(client, private_key, approval_program, clear_program, global_schema, local_schema):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(sender, params, on_complete,
                                           approval_program, clear_program,
                                           global_schema, local_schema)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(
            client, tx_id, 5)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(
            transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response['application-index']
    print("Created new app-id:", app_id)

    return app_id


def create_asset(algod_client, creator_public_key, manager_public_key, creator_private_key, asset_name, unit_name, total_supply):
    params = algod_client.suggested_params()

    txn = AssetConfigTxn(
        sender=creator_public_key,
        sp=params,
        total=total_supply,
        default_frozen=False,
        unit_name=unit_name,
        asset_name=asset_name,
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
        confirmed_txn = transaction.wait_for_confirmation(
            algod_client, txid, 4)
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
        return asset_id
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


def opt_in(algod_client, opt_in_account, opt_in_private_key, asset_id):
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
        txn = transaction.AssetTransferTxn(
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
            confirmed_txn = transaction.wait_for_confirmation(
                algod_client, txid, 4)
            print("TXID: ", txid)
            print("Result confirmed in round: {}".format(
                confirmed_txn['confirmed-round']))

        except Exception as err:
            print(err)
        # Now check the asset holding for that account.
        # This should now show a holding with a balance of 0.
        print_asset_holding(algod_client, opt_in_account, asset_id)


def send_asset(algod_client, asset_id, asset_sender, asset_reciver, sender_private_key):
    params = algod_client.suggested_params()

    txn = AssetTransferTxn(
        sender=asset_sender,
        sp=params,
        receiver=asset_reciver,
        amt=1,
        index=asset_id)
    stxn = txn.sign(sender_private_key)
    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = transaction.wait_for_confirmation(
            algod_client, txid, 4)
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(
            confirmed_txn['confirmed-round']))

    except Exception as err:
        print(err)

    print_asset_holding(algod_client, asset_reciver, asset_id)
