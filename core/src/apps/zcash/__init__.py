from micropython import const

from trezor import wire, protobuf, strings, ui, messages
from trezor.crypto import random
from trezor.crypto import zcash as zcashlib
from trezor.crypto.hashlib import blake2b
from trezor.messages import PrevTx, SignTx, TxInput, TxOutput, TxAckInput, TxAckOutput
from trezor.messages import TxRequest, TxRequestDetailsType, TxRequestSerializedType

from trezor.utils import HashWriter, ensure, BufferReader

from trezor.enums import RequestType
from trezor.enums import ButtonRequestType
from trezor.ui.layouts import (
    confirm_action,
    confirm_blob,
    confirm_metadata,
    confirm_output,
    confirm_properties,
    confirm_text,
)
from trezor.wire import ProcessError


from apps.common.coininfo import CoinInfo
from apps.common.keychain import Keychain
from apps.common.writers import write_bitcoin_varint
from apps.common import readers

from apps.bitcoin.scripts import write_bip143_script_code_prefixed
from apps.bitcoin.writers import (
    TX_HASH_SIZE,
    get_tx_hash,
    write_bytes_fixed,
    write_bytes_reversed,
    write_tx_output,
    write_uint32,
    write_uint64,
)

from apps.bitcoin.sign_tx.matchcheck import MatchChecker
from apps.bitcoin.sign_tx.bitcoinlike import Bitcoinlike
from apps.bitcoin.sign_tx import approvers, helpers
from apps.bitcoin.sign_tx.tx_info import TxInfo

from apps import zcash
from . import zip32
from .layout import UiConfirmOrchardOutput
from trezor import log

if False:
    from typing import Sequence
    from apps.common import coininfo
    from .hash143 import Hash143
    from .tx_info import OriginalTxInfo, TxInfo
    from ..writers import Writer

from .zip244 import Zip244TxHasher

OVERWINTERED = 1 << 31

class ZcashV5(Bitcoinlike):
    def __init__(
        self,
        tx: SignTx,
        keychain,  # TODO: type
        coin: CoinInfo,
        approver: approvers.Approver,
    ) -> None:
        ensure(coin.overwintered)
        if tx.version != 5:
            raise wire.DataError("Unsupported transaction version.")

        self.zip244_hasher = zip244.Zip244TxHasher(tx)
        self.zip244_hasher.initialize(tx)
        self.hash143_created = False

        super().__init__(tx, keychain[0], coin, approver)

        self.tx_req.serialized.orchard = messages.ZcashOrchardData()

        self.orchard_keychain = keychain[1]
        self.orchard_wallet_path = OrchardWalletPathChecker()

        self.alphas = []  # TODO: request alphas from the client

    def create_hash143(self) -> Hash143:
        # we don't create a new instance
        # so this can be returned only once
        assert not self.hash143_created
        return self.zip244_hasher

    async def step1_process_inputs(self):
        await super().step1_process_inputs()
        await self.process_orchard_inputs()

    async def step2_approve_outputs(self):
        await super().step2_approve_outputs()
        await self.approve_orchard_outputs()

    async def step3_verify_inputs(self):
        # We don't check prevouts, because BIP-341 techniques
        # were adapted in ZIP-244 sighash.
        # see: https://github.com/zcash/zips/issues/574

        if self.is_transparent_only():
            await self.verify_original_txs()
        elif self.orig_txs:
            raise ProcessError("Shielded replacement transactions are not supported.")

    async def step4_serialize_inputs(self):
        # shield actions first to get a sighash
        await self.shield_orchard_actions()
        await super().step4_serialize_inputs()

    async def step5_serialize_outputs(self):
        await super().step5_serialize_outputs()
        await self.serialize_empty_sapling_bundle()
        # orchard serialization is up to the client

    async def step6_sign_segwit_inputs(self):
        # transparent inputs were signed in step 4
        await self.sign_orchard_inputs()

    def step7_finish(self):
        await super().step7_finish()

    async def process_orchard_inputs(self):
        hasher = HashWriter(blake2b(outlen=32, personal=b"_orchard_inputs_"))

        for i in range(self.tx_info.tx.orchard.inputs_count):
            txi = await self.get_orchard_input(i)
            hasher.write(protobuf.dump_message_buffer(txi))

            self.orchard_wallet_path.add_input(txi)
            self.approver.add_orchard_input(txi)

        self.orchard_inputs_hash = hasher.get_digest()

    async def approve_orchard_outputs(self):
        hasher = HashWriter(blake2b(outlen=32, personal=b"_orchard_outputs"))

        for i in range(self.tx_info.tx.orchard.outputs_count):
            txo = await self.get_orchard_output(i)
            hasher.write(protobuf.dump_message_buffer(txo))

            if orchard_output_is_change(txo):
                self.approver.add_orchard_change_output(txo)
            else:
                self.approver.add_orchard_external_output(txo)

            # TODO: Confirm change memo
            if not self.orchard_wallet_path.output_matches(txo):
                yield UiConfirmOrchardOutput(txo, self.orchard_multi_acount())

        self.orchard_outputs_hash = hasher.get_digest()

    async def shield_orchard_actions(self):
        seed = random.bytes(32)
        self.tx_req.serialized.orchard.randomness_seed = seed

        rand_config = {
            "seed": seed,
            "pos": 0,
        }

        hasher_in = HashWriter(blake2b(outlen=32, personal=b"_orchard_inputs_"))
        hasher_out = HashWriter(blake2b(outlen=32, personal=b"_orchard_outputs"))

        for i in range(self.orchard_actions_count()):
            action_info = dict()

            if i < self.tx_info.tx.orchard.inputs_count:
                txi = await self.get_orchard_input(i)
                hasher_in.write(protobuf.dump_message_buffer(txi))

                sk = self.orchard_keychain.derive(txi.address_n).spending_key()
                fvk = zcashlib.get_orchard_fvk(sk)
                action_info["spend_info"] = {
                    "fvk": fvk,
                    "note": txi.orchard.note,
                }

            if i < self.tx_info.tx.orchard.outputs_count:
                txo = await self.get_orchard_output(i)
                hasher_out.write(protobuf.dump_message_buffer(txo))

                if orchard_output_is_change(txo):
                    sk = self.orchard_keychain.derive(txo.address_n).spending_key()
                    address = zcashlib.get_orchard_address(sk, 0)
                else:
                    receivers = zcash.address.decode_unified(txo.address)
                    address = receivers.get(zcash.address.ORCHARD)
                    assert address is not None

                action_info["output_info"] = {
                    "ovk_flag": txo.orchard.decryptable,
                    "address": address,
                    "value": txo.amount,
                    "memo": txo.orchard.memo,
                }

                if txo.orchard.decryptable:
                    sk = self.orchard_keychain.derive(txo.address_n).spending_key()
                    fvk = zcashlib.get_orchard_fvk(sk)
                    action_info["output_info"]["fvk"] = fvk

            log.warning(__name__, "processing action info: %s", pretty_str(action_info))
            action = zcashlib.shield(action_info, rand_config)  # on this line the magic happens
            log.warning(__name__, "action: %s", pretty_str(action))
            self.zip244_hasher.orchard.add_action(action)
            log.warning(__name__, "rand_config: pos %s", str(rand_config["pos"]))

            self.alphas.append(action["alpha"])

        if (hasher_in.get_digest() != self.orchard_inputs_hash or
            hasher_out.get_digest() != self.orchard_outputs_hash):
            raise ProcessError("Transaction data changed during the process.")

        # Orchard flags as defined in protocol §7.1 tx v5 format
        flags = 0x00 \
              | 0x01 if self.tx_info.tx.orchard.enable_spends else 0x00 \
              | 0x02 if self.tx_info.tx.orchard.enable_outputs else 0x00

        self.zip244_hasher.orchard.finalize(
            flags=bytes([flags]),  # one byte
            value_balance=self.approver.orchard_balance,
            anchor=self.tx_info.tx.orchard.anchor,
        )

        log.warning(__name__, "step5 - tx finalized")

    async def serialize_empty_sapling_bundle(self):
        write_bitcoin_varint(self.serialized_tx, 0)  # nSpendsSapling
        write_bitcoin_varint(self.serialized_tx, 0)  # nOutputsSapling

    async def sign_orchard_inputs(self):
        for i in range(self.tx_info.tx.orchard.inputs_count):
            txi = await self.get_orchard_input(i)
            alpha = await self.get_orchard_alpha(i)
            sk = self.orchard_keychain.derive(txi.address_n).spending_key()
            sighash = self.zip244_hasher.signature_digest()
            signature = zcashlib.sign(sk, alpha, sighash)
            self.set_serialized_orchard_signature(i, signature)

    async def get_orchard_alpha(self, i):
        return self.alphas[i]

    def set_serialized_orchard_signature(self, i, signature):
        assert self.tx_req.serialized.orchard.signature_index is None
        self.tx_req.serialized.orchard.signature_index = i
        self.tx_req.serialized.orchard.signature = signature
        log.warning(__name__, "sig set")

    async def sign_nonsegwit_input(self, i_sign: int) -> None:
        await self.sign_nonsegwit_bip143_input(i_sign)

    async def get_tx_digest(
        self,
        i: int,
        txi: TxInput,
        tx_info: TxInfo | OriginalTxInfo,
        public_keys: Sequence[bytes | memoryview],
        threshold: int,
        script_pubkey: bytes,
        tx_hash: bytes | None = None,
    ) -> bytes:
        return self.zip244_hasher.txid_digest()

    def write_tx_header(
        self, w: Writer, tx: SignTx | PrevTx, witness_marker: bool
    ) -> None:
        if tx.version_group_id is None:
            raise wire.DataError("Version group ID is missing")
        assert tx.expiry is not None # checked in sanitize_*

        write_uint32(w, tx.version | OVERWINTERED)  # nVersion | fOverwintered
        write_uint32(w, tx.version_group_id)        # nVersionGroupId
        write_uint32(w, tx.branch_id)               # nConsensusBranchId
        write_uint32(w, tx.lock_time)               # lock_time
        write_uint32(w, tx.expiry)                  # expiryHeight

    def write_tx_footer(self, w: Writer, tx: SignTx | PrevTx) -> None:
        pass  # there is no footer in v5 tx format

    async def get_orchard_input(self, i):
        self.tx_req.request_type = RequestType.TXORCHARDINPUT
        self.tx_req.details.request_index = i
        ack = yield TxAckInput, self.tx_req
        _clear_tx_request(self.tx_req)
        return self.sanitize_orchard_input(ack.tx.input)

    async def get_orchard_output(self, i):
        self.tx_req.request_type = RequestType.TXORCHARDOUTPUT
        self.tx_req.details.request_index = i
        ack = yield TxAckOutput, self.tx_req
        _clear_tx_request(self.tx_req)
        return self.sanitize_orchard_output(ack.tx.output)

    def sanitize_orchard_input(self, txi: TxInput):
        # TODO: refuse all unexpected fields
        assert txi.orchard is not None
        assert txi.orig_hash is None  # approver
        assert len(txi.address_n) == ZIP32_WALLET_DEPTH

        # txi.amount equals txi.orchard.note value
        r = BufferReader(txi.orchard.note[43:51])
        txi.amount = readers.read_uint64_le(r)

        return txi

    def sanitize_orchard_output(self, txo: TxOutput):
        # TODO: refuse all unexpected fields
        internal = len(txo.address_n) != 0
        external = txo.address is not None

        # output must be exclusively internal or external
        assert internal ^ external

        if internal:
            # internal outputs must be decryptable
            assert txo.orchard.decryptable == True

        if self.orchard_multi_acount():
            if txo.orchard.decryptable:
                assert txo.orchard.ovk_address_n is not None
        else:
            txo.orchard.ovk_address_n = self.orchard_wallet_path.attribute

        # this is orchard output
        assert txo.orchard is not None

        return txo

    def orchard_actions_count(self):
        if self.tx_info.tx.orchard.inputs_count + self.tx_info.tx.orchard.outputs_count > 0:
            return max(
                2,  # minimal amount of actions
                self.tx_info.tx.orchard.inputs_count,
                self.tx_info.tx.orchard.outputs_count
            )
        else:
            return 0

    def orchard_multi_acount(self):
        """Returns true iff there exists two Orchard spends
        from different accounts."""
        return self.orchard_wallet_path == MatchChecker.MISMATCH

    def is_transparent_only(self):
        return self.orchard_actions_count() == 0


def _clear_tx_request(req):
    helpers._clear_tx_request(req)  # clear transparent fields
    _clear_tx_request_orchard(req)  # clear Orchard fields

def _clear_tx_request_orchard(req):
    req.serialized.orchard.signature_index = None
    req.serialized.orchard.signature = None
    req.serialized.orchard.randomness_seed = None


def pretty_str(obj, ident=""):
    lines = []
    if type(obj) == dict:
        lines.append("{") 
        for k,v in obj.items():
            lines.append("   " + str(k)+ ": " + pretty_str(v, ident + 8*" ") + ",")
        lines.append("}")
        return "\n".join([ident + l for l in lines])
    elif type(obj) == bytes:
        return "bytes(%d)" % len(obj)
    else:
        return str(obj)


def orchard_output_is_change(txo):
    return len(txo.address_n) != 0


ZIP32_WALLET_DEPTH = 3

class OrchardWalletPathChecker(MatchChecker):
    def attribute_from_tx(self, txio: TxInput | TxOutput) -> Any:
        if len(txio.address_n) != ZIP32_WALLET_DEPTH:
            return None
        return txio.address_n


class ZcashApprover(approvers.BasicApprover):
    def __init__(self, *args, **kwargs):
        self.orchard_balance = 0
        super().__init__(*args, **kwargs)

    def add_orchard_input(self, txi: TxInput) -> None:
        self.total_in += txi.amount
        self.orchard_balance += txi.amount

    def add_orchard_change_output(self, txo: TxOutput) -> None:
        self.change_count += 1
        self.total_out += txo.amount
        self.change_out += txo.amount
        self.orchard_balance -= txo.amount

    def add_orchard_external_output(self, txo: TxOutput) -> None:
        self.total_out += txo.amount
        self.orchard_balance -= txo.amount
        # skipped, because confirmation dialog is made by signer
        # await helpers.confirm_output(txo, self.coin, self.amount_unit)

    async def approve_tx(self, _a, _b):
        pass




