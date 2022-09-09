import ecdsa
import base58
import base64
import codecs
import hashlib
from utils import segwit_address


def compress_public_key(public_key):
    pk_bytes = bytes.fromhex(public_key)
    x, y = pk_bytes[:32], pk_bytes[32:]
    parity_flag = (b'\x03' if int(y.hex(), 16) & 1 else b'\x02')
    public_key_compressed = (parity_flag + x).hex()
    return public_key_compressed


def hash160(hex_str):
    sha = hashlib.sha256()
    rip = hashlib.new('ripemd160')
    if type(hex_str) == bytes:
        sha.update(bytearray(hex_str))
    else:
        sha.update(bytearray.fromhex(hex_str))
    rip.update(sha.digest())
    return rip


def doublehash256(hex_str):
    sha = hashlib.sha256()
    if type(hex_str) == bytes:
        sha.update(bytearray(hex_str))
    else:
        sha.update(bytearray.fromhex(hex_str))
    checksum = sha.digest()
    sha = hashlib.sha256()
    sha.update(checksum)
    return sha


def address_p2pkh_address(public_key):
    key_hash = '26' + hash160(public_key).hexdigest()
    checksum = doublehash256(key_hash).hexdigest()[0:8]
    return base58.b58encode(bytes(bytearray.fromhex(key_hash + checksum))).decode('utf-8')


def generate_p2sh_address(public_key):
    prefix_redeem = b'\x00\x14'
    # prefix_redeem = b'\x00'
    redeem_script = hash160(prefix_redeem + hash160(public_key).digest()).digest()  # 20 bytes
    m = b'\x06' + redeem_script
    c = doublehash256(m).digest()[:4]
    return base58.b58encode(m + c).decode('utf-8')


def generate_bech32_address(public_key):
    redeem_script_p2_wpkh = hash160(public_key).digest()
    return str(segwit_address.encode('bg', 0x00, redeem_script_p2_wpkh))


def checksum(v):
    checksum_size = 4
    return doublehash256(v).digest()[:checksum_size]


def sign_message(private_key, message):
    wif_private_key = str(private_key)
    private_key = base58.b58decode(private_key).hex()
    if len(private_key) == 76:
        # compressed private key, drop first byte, and last 4+1 bytes
        private_key = private_key[2:-10]
    else:
        # non-compressed private key, drop first byte, and last 4 bytes
        private_key = private_key[2:-8]

    signing_key = ecdsa.SigningKey.from_string(codecs.decode(private_key, 'hex'),
                                               hashfunc=hashlib.sha256,
                                               curve=ecdsa.SECP256k1)

    verifying_key = signing_key.get_verifying_key().to_string().hex()
    # print(verifying_key)

    public_key_compressed = compress_public_key(verifying_key)
    # print(public_key_compressed)

    sig = signing_key.sign_deterministic(message.encode(), hashfunc=hashlib.sha256)
    return {
        'public_key': verifying_key,
        'public_key_compressed': public_key_compressed,
        'address_p2pkh': address_p2pkh_address(public_key_compressed),
        'address_p2sh': generate_p2sh_address(public_key_compressed),
        'address_bech32': generate_bech32_address(public_key_compressed),
        'signature': base64.b64encode(sig).decode()
    }


def verify_signature(public_key, signature, message):
    verifying_key = ecdsa.VerifyingKey.from_string(codecs.decode(public_key, 'hex'),
                                                   curve=ecdsa.SECP256k1,
                                                   hashfunc=hashlib.sha256)

    # decode signature
    signature = base64.b64decode(signature)

    try:
        # verify signature
        success = verifying_key.verify(signature, message.encode(), hashfunc=hashlib.sha256)
    except:
        success = False

    return success

# sign_message('RaNtWL2tj3VCbcfYnrS5h85acCxR78NxBSsPwzATpoTSgb92B52s', 'test')
# verify_signature('02000993a7d2e090a0dbba6271f1fb8964192196dfb6fdf06dd96a815b851d30f1', 'rO3Y8zpOA29DEgO7mxlYhq/zWXFCF8R8qKp9uw3/c3FLtImpbckpZEJNfeGLm1KhiXIF39XHSzTVqtFsDQymwA==', 'hahahat')
