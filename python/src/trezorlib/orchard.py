# This file is part of the Trezor project.
#
# Copyright (C) 2012-2019 SatoshiLabs and contributors
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the License along with this library.
# If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>.

from . import messages
from .tools import expect

@expect(messages.OrchardTestOutput, field="hello_output")
def test(client):
    hello = client.call(
        messages.OrchardTestInput(hello_input=bytes([ 158, 65, 96, 245, 29, 17, 127, 195, 173, 55, 35, 94, 62, 5, 60, 89, 166, 171, 225, 188,71, 252, 108, 156, 170, 69, 105, 85, 77, 30, 136, 10]))
    )
    return hello