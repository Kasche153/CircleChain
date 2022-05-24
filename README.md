

## CircleChain: Tokenizing Products with a Role-based Scheme for a Circular Economy 
In a circular economy, tracking the flow of second-life components for quality control is critical. Tokenization can enhance the transparency of the flow of second-life components. However, simple tokenization does not correspond to real economic models and lacks the ability to finely manage complex business processes. In particular, existing systems have to take into account the different roles of the parties in the supply chain. Based on the Algorand blockchain, we propose a role-based token management scheme, which can achieve authentication, synthesis, circulation, and reuse of these second-life components in a trustless environment. The proposed scheme not only achieves fine-grained and scalable second-life component management, but also enables on-chain trading, subsidies, and green-bond issuance. Furthermore, we implemented and performed scalability tests for the proposed architecture on Algorand blockchain using its smart contracts and Algorand Standard Assets (ASA). The open-source implementation, tests, along with results are available on our Github page. 
  
  [![arXiv](https://img.shields.io/badge/arXiv-2205.11212-blue.svg)](https://arxiv.org/abs/2205.11212)

### Cite us

```
@misc{https://doi.org/10.48550/arxiv.2205.11212,
  doi = {10.48550/ARXIV.2205.11212},
  
  url = {https://arxiv.org/abs/2205.11212},
  
  author = {Eshghie, Mojtaba and Quan, Li and Kasche, Gustav Andersson and Jacobson, Filip and Bassi, Cosimo and Artho, Cyrille},
  
  keywords = {Distributed, Parallel, and Cluster Computing (cs.DC), Cryptography and Security (cs.CR), Computers and Society (cs.CY), FOS: Computer and information sciences, FOS: Computer and information sciences},
  
  title = {CircleChain: Tokenizing Products with a Role-based Scheme for a Circular Economy},
  
  publisher = {arXiv},
  
  year = {2022},
  
  copyright = {Creative Commons Attribution 4.0 International}
}

```

### What is this?

This is a first implementation of life cycle tracing system (in the context of a circular economy / CE)  built on the Algorand Blockchain
It is implemented to for potentiall use in chip tracing in the IT sector but could potentially be used in other industries as well.
It has been tested using the Algorand Testnet.

### How to try it?

There are some prerequisite for using trying the system.

1. Have Docker installed and running on your machine
2. Start the Algorand Testnet on by using the following command cd sandbox && ./sandbox testnet up
3. Check that the accounts are used have required funding if not use the Algorand testnet faucet to
   fund them.
4. Run python3 contrat.py in the terminal standing in the sandbox folder
5. Read the transaction history of the application accounts on the Algoexplorer.io you been redirected to

### How it works?

1. The contract is created and deployed to the Testnet
2. The contract is funded with 1 Algo from its creator
3. The Authenticator creates the 3 NFTs
4. The computer manufacture opts into the 3 NFTs
5. The Authenticator sends the 3 NFTs to the computer manufacture

6. The contract is called with IDs of the 3 NFTs in the foreign_assets_array
   and the subroutine to opt-in is called for each on.
7. The computer manufacture sends the 3 NFTs to the contract
8. The creator calls the contract with the user address in the foreign_address_array[1]
   which gives the user exclusive rights to invovke step 9
9. The user calls the contract with the recycler address in the foreign_address_array[2]
   which rekeys the contract account to the recycler address.
10. The recycler transfers the 3 NFTs from the contract account address by using its own private_key
    to sign the transfer
