"""Fast, value-based digest of an in-memory JSON tree, never a pickle reader.

The binary encoding stays local to hashing: no serialized object is stored,
accepted from a request or deserialized. Memoization is disabled so that shared
string/dict identities produce the same digest after JSON persistence. JSON
inputs are acyclic. A change in mapping order can cause an extra cache miss,
which is safe; it cannot hide a content change.
"""
import hashlib
import io
import pickle


def digest(value):
    output=io.BytesIO()
    encoder=pickle.Pickler(output,protocol=4)
    encoder.fast=True
    encoder.dump(value)
    return hashlib.sha256(b'tb-public-signature-2\0'+output.getbuffer()).digest()
