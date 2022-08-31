import asyncio
import base64
import json
from pydoc import cli, doc
from turtle import pu
import webbrowser
import datetime
from asgiref.sync import sync_to_async
from algosdk.future import transaction
from algosdk.future.transaction import PaymentTxn, AssetTransferTxn, AssetConfigTxn
from algosdk import account, mnemonic, logic
from algosdk.v2client import algod
from pyteal import *


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

    handle_noop = Cond(
        [And(
            Global.group_size() == Int(1),
            Txn.sender() == Global.creator_address(),
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
