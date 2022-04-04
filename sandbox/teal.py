from pyteal import *


def approval_program():
    program = Return((Int(1)))
    return compileTeal(program, Mode.Application, version=5)


def clear_state_program():
    program = Return(Int(1))
    # Mode.Application specifies that this is a smart contract
    return compileTeal(program, Mode.Application, version=5)


def asset_creation():
    return 1


print(approval_program())
