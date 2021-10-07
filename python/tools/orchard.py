#!/usr/bin/env python3
from trezorlib.client import get_default_client
from trezorlib.orchard import test

client = get_default_client()

hello = test(client)
print(hello)