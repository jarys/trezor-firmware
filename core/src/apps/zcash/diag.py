# if __debug__:

from trezor.messages import DebugZcashDiagRequest, DebugZcashDiagResponse
#from trezor.crypto import random
from trezor.enums import ButtonRequestType
from trezor.ui.layouts import confirm_action, draw_simple_text

from trezor import log

from trezor.crypto import orchardlib

async def diag(ctx: Context, msg: DebugZcashDiagRequest) -> DebugZcashDiagResponse:
    log.warning(__name__, "orchardlib.diag called")
    log.warning(__name__, "ins : {}".format(msg.ins))
    log.warning(__name__, "data: {}".format(msg.data))

    if msg.ins == b"hello":
        await confirm_action(
            ctx,
            "test",
            "Confirm test",
            action="msg: {}".format(msg.data),
            description="continue",
            br_code=ButtonRequestType.ProtectCall,
        )

        return DebugZcashDiagResponse(data=b"Hello from the Trezor!")
    else:
        return DebugZcashDiagResponse(
            data=orchardlib.diag(msg.ins, msg.data)
        )