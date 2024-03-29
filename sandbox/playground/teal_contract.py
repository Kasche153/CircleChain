import base64
from algosdk.future import transaction
from algosdk.future.transaction import PaymentTxn
from algosdk import account, mnemonic, logic
from algosdk.v2client import algod
from pyteal import *


algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


auth_mnemonic = "december giggle gown trap bread soccer sort song judge island lift black bitter ghost impulse rice actress because ribbon unusual negative lucky monster above used"
computer_mnemonic = "amused burger uphold hurt stereo holiday summer inherit believe angry token pledge chicken blush repeat patrol common hungry hello hammer humor ski coach above flight"
recycler_mnemonic = "welcome explain vast blind praise oak fire brush wreck jazz family sweet civil dynamic dance aim arrange bachelor flower earn brother pig giant absent digital"


def approval_program():
    on_creation = Seq([
        App.globalPut(Bytes("User"), Global.zero_address()),
        Return(Int(1))
    ])

    handle_optin = Return(Int(0))

    handle_closeout = Return(Int(0))

    handle_updateapp = Return(Int(0))

    handle_deleteapp = Return(Int(0))

    scratchCount = ScratchVar(TealType.uint64)

    handle_noop = Return(Int(1))

    @ Subroutine(TealType.none)
    def opt_in():
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.asset_receiver: Global.current_application_address(),
                TxnField.asset_amount: Int(0),
                TxnField.xfer_asset: Txn.assets[i.load()],
            }),
            InnerTxnBuilder.Submit())

    i = ScratchVar(TealType.uint64)
    len = ScratchVar(TealType.uint64)

    # release_clause = Or(Txn.accounts[0] == Addr(
    #     "F2VKSSWABZXWZRKGCMTABTKLDIQG6NB47536L6NE6UKOZO4A2XFBOT5ETQ"), Txn.accounts[0] == Addr(
    #     "F2VKSSWABZXWZRKGCMTABTKLDIQG6NB47536L6NE6UKOZO4A2XFBOT5ETQ"))

    init = Seq(
        For(i.store(Int(0)), i.load() < Txn.assets.length(), i.store(i.load() + Int(1))).Do(
            opt_in()
        ),

        Return(Int(1)))

    release = Seq([InnerTxnBuilder.Begin(), InnerTxnBuilder.SetFields({
        TxnField.type_enum: TxnType.Payment,
        TxnField.amount: Int(0),
        TxnField.receiver: Txn.accounts[0],
        TxnField.rekey_to: Txn.accounts[0]

    }), InnerTxnBuilder.Submit(),  Return(Int(1))])

    set_user = Seq([App.globalPut(Bytes("User"),
                                  Txn.accounts[0]), Return(Int(1))])

    handle_noop = Cond(
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("Init")
        ), init],
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("Release"),
            # release_clause,
            Txn.sender() == App.globalGet(Bytes("User")),
        ), release],
        [And(
            Global.group_size() == Int(1),
            App.globalGet(Bytes("User")) == Global.zero_address(),
            Txn.application_args[0] == Bytes("Set user"),

        ), set_user],
    )

    # default transaction sub-types for application
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )

    return compileTeal(program, Mode.Application, version=6)


def clear_state_program():
    program = Return(Int(1))
    # Mode.Application specifies that this is a smart contract
    return compileTeal(program, Mode.Application, version=6)


def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])


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


def deploy_new_application(algod_client, creator_private_key, compiled_teal, compiled_clear_teal):

    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 0
    global_ints = 1
    global_bytes = 5
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    # compile program to TEAL assembly
    with open("./approval.teal", "w") as f:
        approval_program_teal = compiled_teal
        f.write(approval_program_teal)

    # compile program to TEAL assembly
    with open("./clear.teal", "w") as f:
        clear_state_program_teal = compiled_clear_teal
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


# call application
def call_app(client, private_key, index, args):
    # declare sender
    sender = mnemonic.to_public_key(auth_mnemonic)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(
        sender, params, index, app_args=args, foreign_assets=[86442695,  81978905, 83280757], accounts=["F2VKSSWABZXWZRKGCMTABTKLDIQG6NB47536L6NE6UKOZO4A2XFBOT5ETQ", mnemonic.to_public_key(computer_mnemonic),  mnemonic.to_public_key(computer_mnemonic),  mnemonic.to_public_key(computer_mnemonic)])

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


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # define private keys
    creator_private_key = get_private_key_from_mnemonic(computer_mnemonic)

    clear_state = clear_state_program()
    approval = approval_program()

    # # deploy application to the chain for the first time (or get fixed app_id)
    app_id = deploy_new_application(
        algod_client, creator_private_key, approval, clear_state)
    print(logic.get_application_address(app_id))

    # calling application with arguments
    # call_app(algod_client, creator_private_key, app_id, args=["Init"])
    # read global state of application


def call_contract(app_id):
    auth_pk = get_private_key_from_mnemonic(auth_mnemonic)
    algod_client = algod.AlgodClient(algod_token, algod_address)
    call_app(algod_client, auth_pk, app_id, args=["Release"])


# main()
call_contract(86446625)


def algo_transaction(add, key, amount, reciver, algod_client) -> dict:

    params = algod_client.suggested_params()
    unsigned_txn = PaymentTxn(
        add, params, reciver, amount)
    signed = unsigned_txn.sign(key)
    tx_id = algod_client.send_transaction(signed)
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
    return pmtx


# algo_transaction("3WEGUFAW4ZN7HK3L7BFOZ3LSYZLIGWBITUSIPZQLS37COW5WGBUXVQYERQ", key=mnemonic.to_private_key(
#     auth_mnemonic), reciver=mnemonic.to_public_key(computer_mnemonic), amount=1000, algod_client=algod.AlgodClient(algod_token, algod_address)
# )
