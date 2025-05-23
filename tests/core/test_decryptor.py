import pytest
from unittest.mock import patch, Mock
import os
from decryptor import decrypt_data
from Crypto.Cipher import AES


class TestDecryptor:
    """测试解密器模块的测试套件。"""

    def setup_method(self) -> None:
        """设置测试装置。"""
        # AES 密钥示例（16 字节 / 128 位）
        self.key = b'\x01\x23\x45\x67\x89\xAB\xCD\xEF\x01\x23\x45\x67\x89\xAB\xCD\xEF'
        # IV 示例（16 字节 / 128 位）
        self.iv = b'\x12\x34\x56\x78\x90\xAB\xCD\xEF\x12\x34\x56\x78\x90\xAB\xCD\xEF'

    def test_decrypt_data_exact_block_size(self) -> None:
        """测试精确块大小（16 字节）数据的解密。"""
        # 创建加密测试数据（16 字节，恰好一个 AES 块）
        test_encrypted_data = b'\x1a\x2b\x3c\x4d\x5e\x6f\x7a\x8b\x9c\xad\xbe\xcf\xd0\xe1\xf2\x03'

        # 解密数据
        decrypted = decrypt_data(test_encrypted_data, self.key, self.iv)

        # 验证解密的数据不为空并且与输入长度相同
        assert len(decrypted) == len(test_encrypted_data)
        # 我们不验证确切内容，因为在不知道原始明文的情况下我们无法知道预期的输出

    def test_decrypt_data_with_padding(self) -> None:
        """测试需要填充的数据解密（非 16 字节的倍数）。"""
        # 创建加密测试数据（20 字节，不是 16 的倍数）
        test_encrypted_data = b'\x1a\x2b\x3c\x4d\x5e\x6f\x7a\x8b\x9c\xad\xbe\xcf\xd0\xe1\xf2\x03\x04\x05\x06\x07'

        # 使用 last_block=True 解密数据以处理填充
        decrypted = decrypt_data(
            test_encrypted_data, self.key, self.iv, last_block=True)

        # 解密输出应具有原始长度（20 字节）
        assert len(decrypted) == 20

        # 还要测试 last_block=False（应保留填充）
        decrypted_with_padding = decrypt_data(
            test_encrypted_data, self.key, self.iv, last_block=False)

        # 解密输出应被填充为 16 的倍数（32 字节）
        assert len(decrypted_with_padding) == 32

    def test_decrypt_small_data(self) -> None:
        """测试需要填充的非常小的数据解密。"""
        # 创建小型加密测试数据（4 字节）
        test_encrypted_data = b'\x01\x02\x03\x04'

        # 解密数据
        decrypted = decrypt_data(test_encrypted_data, self.key, self.iv)

        # 验证已填充为 16 字节
        assert len(decrypted) == 16

        # 使用 last_block=True 进行测试以删除填充
        decrypted_no_padding = decrypt_data(
            test_encrypted_data, self.key, self.iv, last_block=True)

        # 验证保留了原始长度
        assert len(decrypted_no_padding) == 4

    @patch('Crypto.Cipher.AES.new')
    def test_decrypt_data_with_mocked_cipher(self, mock_aes_new: Mock) -> None:
        """测试使用模拟的 AES 密码进行解密。"""
        # 设置模拟
        mock_cipher = Mock()
        mock_cipher.decrypt.return_value = b'decrypted_content_here'
        mock_aes_new.return_value = mock_cipher

        # 使用一些测试数据调用函数
        result = decrypt_data(b'test_data', self.key, self.iv)

        # 验证使用正确的参数创建了 AES 密码
        assert mock_aes_new.call_args[0][0] == self.key
        assert mock_aes_new.call_args[0][1] == 2  # AES.MODE_CBC 是 2
        assert mock_aes_new.call_args[0][2] == self.iv

        # 验证调用了 mock_cipher.decrypt
        assert mock_cipher.decrypt.called

        # 验证结果匹配我们的模拟返回的内容
        assert result == b'decrypted_content_here'

    def test_decrypt_data_invalid_key_size(self) -> None:
        """测试使用无效密钥大小的解密。"""
        # 无效密钥（不是 16、24 或 32 字节）
        invalid_key = b'\x01\x02\x03'

        # 尝试使用无效密钥解密应返回原始数据
        result = decrypt_data(b'test_data', invalid_key, self.iv)

        # 在错误时应返回原始数据
        assert result == b'test_data'

    def test_decrypt_data_invalid_iv_size(self) -> None:
        """测试使用无效 IV 大小的解密。"""
        # 无效 IV（不是 16 字节）
        invalid_iv = b'\x01\x02\x03'

        # 尝试使用无效 IV 解密应返回原始数据
        result = decrypt_data(b'test_data', self.key, invalid_iv)

        # 在错误时应返回原始数据
        assert result == b'test_data'

    def test_decrypt_empty_data(self) -> None:
        """测试空数据的解密。"""
        # 空数据
        empty_data = b''

        # 尝试解密空数据
        result = decrypt_data(empty_data, self.key, self.iv)

        # 应返回空数据
        assert result == b''

    @pytest.mark.parametrize("data_length", [1, 15, 16, 17, 31, 32, 33])
    def test_decrypt_various_data_lengths(self, data_length: int) -> None:
        """测试各种数据长度的解密。"""
        # 创建特定长度的测试数据
        test_data = os.urandom(data_length)

        # 解密数据
        decrypted = decrypt_data(test_data, self.key, self.iv)

        # 验证长度是 16 的倍数（AES 块大小）
        assert len(decrypted) % 16 == 0

        # 如果设置了 last_block=True，验证我们得到原始长度
        decrypted_last_block = decrypt_data(
            test_data, self.key, self.iv, last_block=True)
        assert len(decrypted_last_block) == data_length

    def test_real_encryption_decryption(self) -> None:
        """测试实际加密后解密。"""

        # 原始明文数据（恰好 16 字节）
        plaintext = b'This is a test!!'

        # 加密数据
        cipher = AES.new(key=self.key, mode=AES.MODE_CBC, # type: ignore
                         iv=self.iv)  # type: ignore
        encrypted_data = cipher.encrypt(plaintext)

        # 现在解密它
        decrypted_data = decrypt_data(encrypted_data, self.key, self.iv)

        # 验证我们得到了原始明文
        assert decrypted_data == plaintext

    def test_real_encryption_decryption_with_padding(self) -> None:
        """测试非块大小数据的实际加密后解密。"""

        # 原始明文数据（不是 16 字节的倍数）
        plaintext = b'This needs padding'

        # 创建用于加密的填充版本
        padding_length = 16 - (len(plaintext) % 16)
        padded_plaintext = plaintext + (b'\x00' * padding_length)

        # 加密填充数据
        cipher = AES.new(key=self.key, mode=AES.MODE_CBC, # type: ignore
                         iv=self.iv)  # type: ignore
        encrypted_data = cipher.encrypt(padded_plaintext)

        # 现在使用 last_block=True 解密它以删除填充
        decrypted_data = decrypt_data(
            encrypted_data, self.key, self.iv, last_block=True)

        # 验证我们得到了没有填充的原始明文
        assert decrypted_data == plaintext


# 如果直接执行文件，则运行测试
if __name__ == "__main__":
    pytest.main(["-v", __file__])
