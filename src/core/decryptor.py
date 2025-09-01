from loguru import logger
from Crypto.Cipher import AES


def decrypt_data(data: bytes, key: bytes, iv: bytes, last_block: bool = False) -> bytes:
    """
    Decrypt AES-encrypted data block

    Args:
        data (bytes): Data to be decrypted
        key (bytes): AES key
        iv (bytes): Initialization vector
        last_block (bool): Whether this is the last data block

    Returns:
        bytes: Decrypted data
    """
    try:
        # Create decryptor
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # Ensure data length is a multiple of 16 bytes
        pad_len = len(data) % 16
        padded_data = data
        if pad_len != 0:
            # Add PKCS#7 padding
            padded_data = data + b'\x00' * (16 - pad_len)

        # Decrypt data
        decrypted_data = cipher.decrypt(padded_data)

        # If this is the last block and there's padding, remove it
        if last_block and pad_len != 0:
            # Keep only the original length data
            return bytes(decrypted_data[:-pad_len])

        return bytes(decrypted_data)

    except Exception as e:
        logger.error(f"Error decrypting data: {e}", exc_info=True)
        logger.debug(f"Failed data length: {len(data)}, IV length: {len(iv)}")
        return data  # Return original data on decryption failure
