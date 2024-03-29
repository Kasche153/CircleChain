import asyncio
import base64
import json
from pydoc import doc
import webbrowser
import datetime
from asgiref.sync import sync_to_async
from algosdk.future import transaction
from algosdk.future.transaction import PaymentTxn, AssetTransferTxn, AssetConfigTxn
from algosdk import account, mnemonic, logic
from algosdk.v2client import algod
from pyteal import *

algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
# algod_address = "http://localhost:8112"
# algod_token = "1a24068f71c751badae176443e7304ff918c802c938127a9b8e577635a87176f"


# Never share mnemonic and private key. Production environments require stringent private key management.
auth_mnemonic = "twist memory couple draft crazy police nice supply interest field label junior one obscure salt essence rather chicken warrior female universe canoe spell abandon once"
computer_mnemonic = "village canyon short mobile thank blush broken grass silent tragic step bulk huge gate hospital govern include pill sadness long hope forget eight above voice"
user_mnemonic = "tell timber scorpion material horror sweet loop erupt bonus grace slice conduct history sausage unable cliff right frozen pistol fault squeeze work basic absorb spell"
recycler_mnemonic = "ill visual despair industry lizard shoe forum lecture draft half motor discover satoshi gaze mango vehicle immense collect across comfort lumber globe card abstract submit"


auth_add = mnemonic.to_public_key(auth_mnemonic)
computer_add = mnemonic.to_public_key(computer_mnemonic)
user_add = mnemonic.to_public_key(user_mnemonic)
recycler_add = mnemonic.to_public_key(recycler_mnemonic)

auth_key = mnemonic.to_private_key(auth_mnemonic)
computer_key = mnemonic.to_private_key(computer_mnemonic)
user_key = mnemonic.to_private_key(user_mnemonic)
recycler_key = mnemonic.to_private_key(recycler_mnemonic)


def approval_program(recyclers):
    on_creation = Seq([
        App.globalPut(Bytes("User"), Global.zero_address()),
        App.globalPut(Bytes("Recycler1"), Addr(recyclers[0])),
        App.globalPut(Bytes("Recycler2"), Addr(recyclers[1])),
        App.globalPut(Bytes("Recycler3"), Addr(recyclers[2])),
        App.globalPut(Bytes("Recycler4"), Addr(recyclers[3])),
        App.globalPut(Bytes("Recycler5"), Addr(recyclers[4])),
        Return(Int(1))
    ])

    handle_optin = Return(Int(0))

    handle_closeout = Return(Int(0))

    handle_updateapp = Return(Int(0))

    handle_deleteapp = Return(Int(0))

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

    release_clause = Or(
        App.globalGet(Bytes("Recycler1")) == Txn.accounts[2],
        App.globalGet(Bytes("Recycler2")) == Txn.accounts[2],
        App.globalGet(Bytes("Recycler3")) == Txn.accounts[2],
        App.globalGet(Bytes("Recycler4")) == Txn.accounts[2],
        App.globalGet(Bytes("Recycler5")) == Txn.accounts[2])

    init = Seq(
        For(i.store(Int(0)), i.load() < Txn.assets.length(), i.store(i.load() + Int(1))).Do(
            opt_in()
        ),

        Return(Int(1)))

    release = Seq([InnerTxnBuilder.Begin(), InnerTxnBuilder.SetFields({
        TxnField.type_enum: TxnType.Payment,
        TxnField.amount: Int(0),
        TxnField.receiver: Txn.accounts[0],
        TxnField.rekey_to: Txn.accounts[2]

    }), InnerTxnBuilder.Submit(),  Return(Int(1))])

    set_user = Seq([App.globalPut(Bytes("User"),
                                  Txn.accounts[1]), Return(Int(1))])

    Global.creator_address()

    handle_noop = Cond(
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("Init")
        ), init],
        [And(
            Global.group_size() == Int(1),
            Txn.application_args[0] == Bytes("Release"),
            release_clause,
            Txn.sender() == App.globalGet(Bytes("User")),
        ), release],
        [And(
            Global.group_size() == Int(1),
            App.globalGet(Bytes("User")) == Global.zero_address(),
            Txn.sender() == Global.creator_address(),
            Txn.application_args[0] == Bytes("Set user"),

        ), set_user],
    )

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

    return compileTeal(program, Mode.Application, version=6)


def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])


def create_app(client, private_key, approval_program, clear_program, global_schema, local_schema):
    sender = account.address_from_private_key(private_key)

    on_complete = transaction.OnComplete.NoOpOC.real

    params = client.suggested_params()

    txn = transaction.ApplicationCreateTxn(sender, params, on_complete,
                                           approval_program, clear_program,
                                           global_schema, local_schema)

    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    client.send_transactions([signed_txn])

    try:
        transaction_response = transaction.wait_for_confirmation(
            client, tx_id, 5)
        # print("TXID: ", tx_id)
        # print("Result confirmed in round: {}".format(
        #    transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response['application-index']
    print("*******    Created new app-id: {}    *******".format(app_id))

    return app_id


def deploy_new_application(algod_client, creator_private_key, compiled_teal, compiled_clear_teal):

    local_ints = 0
    local_bytes = 0
    global_ints = 1
    global_bytes = 16
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    with open("./approval.teal", "w") as f:
        approval_program_teal = compiled_teal
        f.write(approval_program_teal)

    with open("./clear.teal", "w") as f:
        clear_state_program_teal = compiled_clear_teal
        f.write(clear_state_program_teal)

    approval_program_compiled = compile_program(
        algod_client, approval_program_teal)

    clear_state_program_compiled = compile_program(
        algod_client, clear_state_program_teal)

    print("Deploying application......")

    app_id = create_app(algod_client, creator_private_key, approval_program_compiled,
                        clear_state_program_compiled, global_schema, local_schema)

    return app_id


def call_app(client, public_key, private_key, app_id, args, assets=[]):

    params = client.suggested_params()

    txn = transaction.ApplicationNoOpTxn(
        public_key, params, app_id, app_args=args, foreign_assets=assets, accounts=[user_add, recycler_add])

    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    client.send_transactions([signed_txn])

    try:
        transaction_response = transaction.wait_for_confirmation(
            client, tx_id, 4)
        # print("TXID: ", tx_id)
        # print("Result confirmed in round: {}".format(
        #    transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return
    # print("Application called")


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def algo_transaction(add, key, amount, reciver, algod_client) -> dict:

    params = algod_client.suggested_params()
    unsigned_txn = PaymentTxn(
        add, params, reciver, amount)
    signed = unsigned_txn.sign(key)
    tx_id = algod_client.send_transaction(signed)
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 5)
    return pmtx


def call_contract(app_id, args, private_key, public_key, assets=[]):
    algod_client = algod.AlgodClient(algod_token, algod_address)
    call_app(algod_client, public_key=public_key, app_id=app_id,
             private_key=private_key, args=[args], assets=assets)


async def send_asset(algod_client, asset_id, asset_sender, asset_reciver, sender_private_key):
    params = algod_client.suggested_params()
    txn = await sync_to_async(AssetTransferTxn)(
        sender=asset_sender,
        sp=params,
        receiver=asset_reciver,
        amt=1,
        index=asset_id)
    stxn = await sync_to_async(txn.sign)(sender_private_key)
    try:
        txid = await sync_to_async(algod_client.send_transaction)(stxn)
        await sync_to_async(transaction.wait_for_confirmation)(
            algod_client, txid, 4)
        # print("TXID: ", txid)
        # print("Result confirmed in round: {}".format(
        #    confirmed_txn['confirmed-round']))

    except Exception as err:
        print(err)


async def opt_in(algod_client, opt_in_account, opt_in_private_key, asset_id):
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
        txn = await sync_to_async(transaction.AssetTransferTxn)(
            sender=opt_in_account,
            sp=params,
            receiver=opt_in_account,
            amt=0,
            index=asset_id)
        stxn = await sync_to_async(txn.sign)(opt_in_private_key)
        # Send the transaction to the network and retrieve the txid.
        try:
            txid = algod_client.send_transaction(stxn)
            # print("Signed transaction with txID: {}".format(txid))
            # Wait for the transaction to be confirmed
            confirmed_txn = await sync_to_async(transaction.wait_for_confirmation)(
                algod_client, txid, 4)
            # print("TXID: ", txid)
            # print("Result confirmed in round: {}".format(

            #    confirmed_txn['confirmed-round']))

        except Exception as err:
            print(err)
        # Now check the asset holding for that account.
        # This should now show a holding with a balance of 0.


async def create_asset(algod_client, creator_public_key, manager_public_key, creator_private_key, asset_name, unit_name, total_supply, i):
    print('create_asset function started... (for i-th assset: {})'.format(i))
    params = await sync_to_async(algod_client.suggested_params)()

    txn = await sync_to_async(AssetConfigTxn)(
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

    stxn = await sync_to_async(txn.sign)(creator_private_key)

    try:
        print('checkpoint #1 (for i-th assset: {})'.format(i))
        # txid = await algod_client.send_transaction(stxn)
        txid = await sync_to_async(algod_client.send_transaction)(stxn)

        print('checkpoint #2 (for i-th assset: {})'.format(i))
        # confirmed_txn = await transaction.wait_for_confirmation(algod_client, txid, 4)
        confirmed_txn = await sync_to_async(transaction.wait_for_confirmation)(
            algod_client, txid, 4)
        ptx = algod_client.pending_transaction_info(txid)

        print('checkpoint #3 (for i-th assset: {})'.format(i))
        return ptx["asset-index"]
        # print("TXID: ", txid)
        # print("Result confirmed in round: {}".format(
        #    confirmed_txn['confirmed-round']))

    except Exception as err:
        print(err)

    # print("Transaction information: {}".format(
    #    json.dumps(confirmed_txn, indent=4)))


def main():
    algod_client = algod.AlgodClient(algod_token, algod_address)
    clear_state = clear_state_program()
    print('#  moj: clear_state function called successfully')

    approval = approval_program([mnemonic.to_public_key(recycler_mnemonic), mnemonic.to_public_key(recycler_mnemonic), mnemonic.to_public_key(
        recycler_mnemonic), mnemonic.to_public_key(recycler_mnemonic), mnemonic.to_public_key(recycler_mnemonic), mnemonic.to_public_key(recycler_mnemonic)])
    print('#  moj: approval_program function called successfully')

    print('#  moj: computer address is: {}'.format(computer_add))
    app_id = deploy_new_application(
        algod_client, computer_key, approval, clear_state)

    print('#  moj: deploy_new_application called successfully')

    algo_transaction(add=computer_add, key=computer_key,
                     reciver=logic.get_application_address(appID=app_id), amount=10000000, algod_client=algod_client)

    async def create_assets(assets_number):
        return await asyncio.gather(*[create_asset(creator_public_key=auth_add, creator_private_key=auth_key,
                                                   asset_name="CircleChain", unit_name="CC{}".format(i+1), algod_client=algod_client, manager_public_key=auth_add,
                                                   total_supply=1, i=i) for i in range(assets_number)])

    async def opt_in_list(assets, opt_in_accout, opt_in_key):
        return await asyncio.gather(*[opt_in(algod_client=algod_client, asset_id=x, opt_in_account=opt_in_accout, opt_in_private_key=opt_in_key) for x in assets])

    async def send_asset_list(assets, asset_sender, asset_sender_key, asset_reciever):
        return await asyncio.gather(*[send_asset(algod_client=algod_client, asset_id=x, asset_reciver=asset_reciever, asset_sender=asset_sender, sender_private_key=asset_sender_key) for x in assets])

    experiment_size = 20
    step_size = 10
    experiment_output = dict()
    assets_ids = []
    counter = 0
    total_start = datetime.datetime.now()

    for i in range(int(experiment_size / step_size)):
        assets_number = (i + 1) * step_size
        start = datetime.datetime.now()

        print('authenticator address is: {}', auth_add)

        test = asyncio.run(create_assets(assets_number))
        assets_ids.extend(test)
        print(test)

        end = datetime.datetime.now()
        experiment_output[assets_number] = (end - start).total_seconds()

        print('---------------------------------------------------------------------------------')
        print(
            '----- total amount of time spent to create {0} assets: {1}'.format(assets_number, end - start))
    print(experiment_output)
    print(assets_ids)
    print(app_id)
    print(logic.get_application_address(app_id))
    print("gus : checkpoint 1")

    asyncio.run(opt_in_list(assets=assets_ids,
                opt_in_accout=computer_add, opt_in_key=computer_key))
    print("gus : checkpoint 2")

    asyncio.run(send_asset_list(asset_sender=auth_add,
                asset_sender_key=auth_key, assets=assets_ids, asset_reciever=computer_add))

    print("gus : checkpoint 3")

    chunk_size = 6
    for i in range(0, len(assets_ids), chunk_size):
        temp = assets_ids[i:i+chunk_size]
        print(temp)
        call_contract(app_id=app_id, args="Init", assets=temp,
                      private_key=computer_key, public_key=computer_add)
    print("gus : checkpoint 4")

    asyncio.run(send_asset_list(
        assets=assets_ids,
                asset_sender_key=computer_key, asset_sender=computer_add, asset_reciever=logic.get_application_address(app_id)))
    print("gus : checkpoint 5")

    call_contract(app_id=app_id, args="Set user", assets=[],
                  private_key=computer_key, public_key=computer_add)
    print("gus : checkpoint 6")

    call_contract(app_id=app_id, args="Release", assets=[],
                  private_key=user_key, public_key=user_add)
    print("gus : checkpoint 7")

    asyncio.run(send_asset_list(
        assets=assets_ids,
        asset_reciever=auth_add, asset_sender_key=recycler_key, asset_sender=logic.get_application_address(app_id)))
    total_end = datetime.datetime.now()

    print('---------------------------------------------------------------------------------')
    print(
        '----- Circle time:')
    print((total_end - total_start).total_seconds())


main()
