from trezor.messages import OrchardTestInput, OrchardTestOutput
from trezor.crypto import random
from trezor.enums import ButtonRequestType
from trezor.ui.layouts import confirm_action, draw_simple_text

import trezororchard

if False:
    from trezor.wire import Context


async def test(ctx: Context, msg: OrchardTestInput) -> OrchardTestOutput:
    await confirm_action(
        ctx,
        "test",
        "Confirm test",
        action="msg: {}".format(msg.hello_input),
        description="continue",
        br_code=ButtonRequestType.ProtectCall,
    )
    # _ = str(orchard.shield(1)) # call extern C
    m = str(trezororchard.shield(b"9"*32)) # call extern Rust

    return OrchardTestOutput(hello_output=b"Hello for the Trezor!" + m) 