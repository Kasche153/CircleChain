import base64
from re import M

from algosdk.future import transaction
from algosdk import mnemonic
from algosdk.v2client import algod
from pyteal import *
from utils import algo_transaction


auth_mnemonic = "december giggle gown trap bread soccer sort song judge island lift black bitter ghost impulse rice actress because ribbon unusual negative lucky monster above used"
computer_mnemonic = "amused burger uphold hurt stereo holiday summer inherit believe angry token pledge chicken blush repeat patrol common hungry hello hammer humor ski coach above flight"
recycler_mnemonic = "welcome explain vast blind praise oak fire brush wreck jazz family sweet civil dynamic dance aim arrange bachelor flower earn brother pig giant absent digital"


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


def lsig_payment_txn(escrowProg, escrow_address, algod_client, assetId):
    params = algod_client.suggested_params()
    unsigned_txn = transaction.AssetOptInTxn(
        index=assetId, sp=params, sender=escrow_address)
    encodedProg = escrowProg.encode()
    program = base64.decodebytes(encodedProg)
    lsig = transaction.LogicSig(program)
    stxn = transaction.LogicSigTransaction(unsigned_txn, lsig)
    tx_id = algod_client.send_transaction(stxn)
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 10)
    return pmtx


"""Basic Donation Escrow"""

# This should become a NFT escrow with logic that opts-in if the sender is computer company
# and releases if and only if the reciver is the recyler

# WORK IN PROGRESS TODO HANDLE ARGUMENTS FOR OPT_IN VS RELEASE


def recyling_escrow(recycler_address, nfts):
    Fee = Int(1000)

    opt_in = And(
        Txn.type_enum() == TxnType.AssetTransfer,
        Txn.fee() <= Fee,
        Txn.receiver() == Txn.asset_sender(),
        Global.group_size() == Int(1),
        Txn.rekey_to() == Global.zero_address()
    )

    program = Cond(
        [Int(1) == Int(1), opt_in],
    )
    print(compileTeal(program, Mode.Signature, version=5))
    # Mode.Signature specifies that this is a smart signature
    return compileTeal(program, Mode.Signature, version=5)


def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # define public keys
    recycler_pk = mnemonic.to_public_key(recycler_mnemonic)
    computer_pk = mnemonic.to_public_key(computer_mnemonic)
    auth_pk = mnemonic.to_public_key(auth_mnemonic)

    print("--------------------------------------------")
    print("Compiling Donation Smart Signature......")

    stateless_program_teal = recyling_escrow(recycler_pk, 1010)

    escrow_result, escrow_address = compile_smart_signature(
        algod_client, stateless_program_teal)

    print("Program:", escrow_result)
    print("hash: ", escrow_address)

    print("--------------------------------------------")
    print("Activating NFT Smart Signature......")

    # This should become AssetFunding from computer_company
    # Activate escrow contract by sending 2 algo and 1000 microalgo for transaction fee from creator
    amt = 1001000
    algo_transaction(computer_mnemonic, amt, escrow_address, algod_client)

    print("--------------------------------------------")
    print("Optin smart signature......")

    asset_id = 83283929
    lsig_payment_txn(escrow_result, escrow_address,
                     algod_client, asset_id)


main()
