import base64

from algosdk.future import transaction
from algosdk import account, mnemonic, logic
from algosdk.v2client import algod
from pyteal import *


mnemonic1 = "december giggle gown trap bread soccer sort song judge island lift black bitter ghost impulse rice actress because ribbon unusual negative lucky monster above used"
mnemonic2 = "welcome explain vast blind praise oak fire brush wreck jazz family sweet civil dynamic dance aim arrange bachelor flower earn brother pig giant absent digital"
mnemonic3 = "amused burger uphold hurt stereo holiday summer inherit believe angry token pledge chicken blush repeat patrol common hungry hello hammer humor ski coach above flight"

accounts = {}
counter = 1
for m in [mnemonic1, mnemonic2, mnemonic3]:
    accounts[counter] = {}
    accounts[counter]['pk'] = mnemonic.to_public_key(m)
    accounts[counter]['sk'] = mnemonic.to_private_key(m)
    counter += 1


algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def approval_program():

    on_creation = Seq([
        Return(Int(1))
    ])

    handle_optin = Return(Int(0))

    handle_closeout = Return(Int(0))

    handle_updateapp = Return(Int(0))

    handle_deleteapp = Return(Int(0))

    scratchCount = ScratchVar(TealType.uint64)

    release_funds = Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.amount: Int(5000),
            TxnField.receiver: Txn.accounts[1]
        }),
        InnerTxnBuilder.Submit(),
        Return(Int(1))
    ])

    handle_noop = Cond(
        [And(
            Global.group_size() == Int(1),
        ), release_funds],
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )
    # Mode.Application specifies that this is a smart contract
    return compileTeal(program, Mode.Application, version=5)


def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])

# helper function that converts a mnemonic passphrase into a private signing key


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def clear_state_program():
    program = Return(Int(1))
    # Mode.Application specifies that this is a smart contract
    return compileTeal(program, Mode.Application, version=5)


# create new application
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


def deploy_new_application(algod_client, creator_private_key):

    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 0
    global_ints = 1
    global_bytes = 0
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    # compile program to TEAL assembly
    with open("./approval.teal", "w") as f:
        approval_program_teal = approval_program()
        f.write(approval_program_teal)

    # compile program to TEAL assembly
    with open("./clear.teal", "w") as f:
        clear_state_program_teal = clear_state_program()
        f.write(clear_state_program_teal)

    # compile program to binary
    approval_program_compiled = compile_program(
        algod_client, approval_program_teal)

    # compile program to binary
    clear_state_program_compiled = compile_program(
        algod_client, clear_state_program_teal)

    print("--------------------------------------------")
    print("Deploying Counter application......")

    # create new application on the blockchain
    app_id = create_app(algod_client, creator_private_key, approval_program_compiled,
                        clear_state_program_compiled, global_schema, local_schema)
    # app_id = 82012418

    return app_id


# call application
def call_app(client, private_key, index, reciver_account):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(sender, params, index, accounts=[
                                         reciver_account])

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(
            client, tx_id, 4)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(
            transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return
    print("Application called")


def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # define private keys
    creator_private_key = accounts[1]['sk']

    # deploy application to the chain for the first time (or get fixed app_id)
    # app_id = deploy_new_application(algod_client, creator_private_key)
    # app_id = 82222624
    # app_id = 82232359

    # # calling application with arguments
    #
    reciver_account = "4S3LPNMZEHTJHPK7DJXHTV2UAQ4C2347IOTYPEMZVKYO2OECPYC7HKCJYE"
    call_app(algod_client, creator_private_key, 82244095, reciver_account)
    # # read global state of application


main()
