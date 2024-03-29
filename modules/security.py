import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


def generate_key():
    return get_random_bytes(16)  # 128-bit key for AES


class AESCipher:
    def __init__(self, key, hex_mode: bool = False):
        if hex_mode:
            self.key = bytes.fromhex(key)
        else:
            self.key = key

    def encrypt_text(self, text):
        cipher = AES.new(self.key, AES.MODE_CBC)
        padded_text = pad(text.encode(), AES.block_size)
        ciphertext = cipher.encrypt(padded_text)
        return base64.b64encode(cipher.iv + ciphertext)

    def decrypt_text(self, ciphertext):
        ciphertext = base64.b64decode(ciphertext)
        iv = ciphertext[:AES.block_size]
        ciphertext = ciphertext[AES.block_size:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted_text = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted_text.decode()


if __name__ == '__main__':
    text = "Hello, this is a secret message!"
    key = generate_key()
    hex_key = key.hex()
    print("hex key: ", hex_key)
    print("byte key: ", key)

    cipher = AESCipher(hex_key, True)

    encrypted_text = cipher.encrypt_text(text)
    print("Encrypted Text:", encrypted_text)

    decrypted_text = cipher.decrypt_text(encrypted_text)
    print("Decrypted Text:", decrypted_text)
