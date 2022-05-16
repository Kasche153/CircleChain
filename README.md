### WHAT IS THIS

This is a first implementation of life cycle tracing system built on the Algorand Blockchain
It is implemented to for potentiall use in chip tracing in the IT sector but could potentially
be used in other industries aswell.
It has been tested using the Algorand Testnet

### HOW TO TRY IT

There are some prerequisite for using trying the system.

1. Have Docker installed and running on your machine
2. Start the Algorand Testnet on by using the following command cd sandbox && ./sandbox testnet up
3. Check that the accounts are used have required funding if not use the Algorand testnet faucet to
   fund them.
4. Run python3 contrat.py in the terminal standing in the sandbox folder
5. Read the transaction history of the application accounts on the Algoexplorer.io you been redirected to

### HOW IT WORKS

1. The contract is created and deployed to the Testnet
2. The contract is funded with 1 Algo from its creator
3. 3 NFTs are created.
4. The contract is called with IDs of the 3 NFTs in the foreign_assets_array
   and the subroutine to opt-in is called for each on.
5. The NFT creator sends the 3 NFTs to the contract
6. The creator calls the contract with the user address in the foreign_address_array[1]
   which gives the user exclusive rights to invovke step 7
7. The user calls the contract with the recycler address in the foreign_address_array[2]
   which rekeys the contract account to the recycler address.
8. The recycler transfers the 3 NFTs from the account address by using its own private_key
   to sign the transfer
