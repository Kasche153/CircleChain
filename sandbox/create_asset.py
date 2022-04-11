from algosdk import mnemonic
from algosdk.v2client import algod
from utils import create_asset, opt_in, send_asset


auth_mnemonic = "december giggle gown trap bread soccer sort song judge island lift black bitter ghost impulse rice actress because ribbon unusual negative lucky monster above used"
computer_mnemonic = "amused burger uphold hurt stereo holiday summer inherit believe angry token pledge chicken blush repeat patrol common hungry hello hammer humor ski coach above flight"
recycler_mnemonic = "welcome explain vast blind praise oak fire brush wreck jazz family sweet civil dynamic dance aim arrange bachelor flower earn brother pig giant absent digital"


# user declared algod connection parameters. Node must have EnableDeveloperAPI set to true in its config
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def main():
    # Setting up keys and client
    auth_pk = mnemonic.to_public_key(auth_mnemonic)
    auth_sk = mnemonic.to_private_key(auth_mnemonic)
    computer_pk = mnemonic.to_public_key(computer_mnemonic)
    computer_sk = mnemonic.to_private_key(computer_mnemonic)
    algod_client = algod.AlgodClient(
        algod_token=algod_token, algod_address=algod_address)

    # Creating an NFT asset
    asset_id = create_asset(asset_name="Testing utils", manager_public_key=auth_pk, algod_client=algod_client,
                            creator_public_key=auth_pk, creator_private_key=auth_sk, unit_name="plop2", total_supply=1)

    # Opt in to NFT asset using asset_id and keys

    opt_in(opt_in_account=computer_pk, opt_in_private_key=computer_sk,
           algod_client=algod_client, asset_id=asset_id)

    # Send asset from creator to reciver

    send_asset(sender_private_key=auth_sk, asset_sender=auth_pk,
               asset_reciver=computer_pk, algod_client=algod_client, asset_id=asset_id)

    print("I finshed")


main()
