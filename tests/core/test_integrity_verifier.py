"""
Tests for content integrity verification
"""

import pytest
import tempfile
import os
import hashlib
from unittest.mock import Mock, patch

from src.core.integrity_verifier import (
    ContentIntegrityVerifier, IntegrityLevel, IntegrityResult, 
    content_integrity_verifier
)


class TestIntegrityLevel:
    """Test IntegrityLevel enum"""
    
    def test_integrity_levels(self):
        """Test IntegrityLevel enum values"""
        assert IntegrityLevel.BASIC.value == "basic"
        assert IntegrityLevel.STANDARD.value == "standard"
        assert IntegrityLevel.STRICT.value == "strict"
        assert IntegrityLevel.PARANOID.value == "paranoid"


class TestIntegrityResult:
    """Test IntegrityResult dataclass"""
    
    def test_integrity_result_valid(self):
        """Test IntegrityResult for valid content"""
        result = IntegrityResult(
            file_path="/path/to/file.ts",
            is_valid=True,
            integrity_level=IntegrityLevel.STANDARD,
            checks_performed=["size", "hash", "format"],
            error_message="",
            warnings=[]
        )
        
        assert result.file_path == "/path/to/file.ts"
        assert result.is_valid is True
        assert result.integrity_level == IntegrityLevel.STANDARD
        assert "size" in result.checks_performed
        assert "hash" in result.checks_performed
        assert "format" in result.checks_performed
        assert result.error_message == ""
        assert result.warnings == []
        assert result.verification_time > 0
    
    def test_integrity_result_invalid(self):
        """Test IntegrityResult for invalid content"""
        result = IntegrityResult(
            file_path="/path/to/corrupted.ts",
            is_valid=False,
            integrity_level=IntegrityLevel.STRICT,
            checks_performed=["size", "hash"],
            error_message="Hash mismatch detected",
            warnings=["File size suspicious"]
        )
        
        assert result.file_path == "/path/to/corrupted.ts"
        assert result.is_valid is False
        assert result.integrity_level == IntegrityLevel.STRICT
        assert result.error_message == "Hash mismatch detected"
        assert "File size suspicious" in result.warnings
    
    def test_has_warnings(self):
        """Test has_warnings method"""
        result_no_warnings = IntegrityResult(
            file_path="/path/to/file.ts", is_valid=True,
            integrity_level=IntegrityLevel.BASIC, checks_performed=[],
            error_message="", warnings=[]
        )
        
        result_with_warnings = IntegrityResult(
            file_path="/path/to/file.ts", is_valid=True,
            integrity_level=IntegrityLevel.BASIC, checks_performed=[],
            error_message="", warnings=["Minor issue detected"]
        )
        
        assert not result_no_warnings.has_warnings()
        assert result_with_warnings.has_warnings()


class TestContentIntegrityVerifier:
    """Test ContentIntegrityVerifier class"""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing"""
        fd, path = tempfile.mkstemp(suffix=".ts")
        test_data = b"Test content for integrity verification"
        os.write(fd, test_data)
        os.close(fd)
        yield path, test_data
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def verifier(self):
        """Create a fresh ContentIntegrityVerifier for testing"""
        return ContentIntegrityVerifier()
    
    def test_initialization(self, verifier):
        """Test ContentIntegrityVerifier initialization"""
        assert verifier.verification_stats == {
            "total_verifications": 0,
            "successful_verifications": 0,
            "failed_verifications": 0,
            "warnings_count": 0
        }
        assert verifier.hash_algorithms == ["md5", "sha1", "sha256"]
        assert verifier.max_file_size == 100 * 1024 * 1024  # 100MB
    
    def test_verify_file_integrity_basic(self, verifier, temp_file):
        """Test basic file integrity verification"""
        file_path, test_data = temp_file
        expected_hash = hashlib.md5(test_data).hexdigest()
        
        result = verifier.verify_file_integrity(
            file_path, expected_hash, IntegrityLevel.BASIC
        )
        
        assert isinstance(result, IntegrityResult)
        assert result.file_path == file_path
        assert result.is_valid is True
        assert result.integrity_level == IntegrityLevel.BASIC
        assert "size" in result.checks_performed
        assert result.error_message == ""
    
    def test_verify_file_integrity_standard(self, verifier, temp_file):
        """Test standard file integrity verification"""
        file_path, test_data = temp_file
        expected_hash = hashlib.md5(test_data).hexdigest()
        
        result = verifier.verify_file_integrity(
            file_path, expected_hash, IntegrityLevel.STANDARD
        )
        
        assert result.is_valid is True
        assert result.integrity_level == IntegrityLevel.STANDARD
        assert "size" in result.checks_performed
        assert "hash" in result.checks_performed
    
    def test_verify_file_integrity_strict(self, verifier, temp_file):
        """Test strict file integrity verification"""
        file_path, test_data = temp_file
        expected_hash = hashlib.sha256(test_data).hexdigest()
        
        result = verifier.verify_file_integrity(
            file_path, expected_hash, IntegrityLevel.STRICT, hash_algorithm="sha256"
        )
        
        assert result.is_valid is True
        assert result.integrity_level == IntegrityLevel.STRICT
        assert "size" in result.checks_performed
        assert "hash" in result.checks_performed
        assert "format" in result.checks_performed
    
    def test_verify_file_integrity_paranoid(self, verifier, temp_file):
        """Test paranoid file integrity verification"""
        file_path, test_data = temp_file
        expected_hash = hashlib.sha256(test_data).hexdigest()
        
        result = verifier.verify_file_integrity(
            file_path, expected_hash, IntegrityLevel.PARANOID, hash_algorithm="sha256"
        )
        
        assert result.integrity_level == IntegrityLevel.PARANOID
        assert "size" in result.checks_performed
        assert "hash" in result.checks_performed
        assert "format" in result.checks_performed
        assert "multiple_hash" in result.checks_performed
    
    def test_verify_file_integrity_nonexistent_file(self, verifier):
        """Test verification of non-existent file"""
        nonexistent_file = "/path/to/nonexistent/file.ts"
        
        result = verifier.verify_file_integrity(nonexistent_file, "dummy_hash")
        
        assert result.file_path == nonexistent_file
        assert result.is_valid is False
        assert "File does not exist" in result.error_message
    
    def test_verify_file_integrity_hash_mismatch(self, verifier, temp_file):
        """Test verification with hash mismatch"""
        file_path, test_data = temp_file
        wrong_hash = "wrong_hash_value"
        
        result = verifier.verify_file_integrity(
            file_path, wrong_hash, IntegrityLevel.STANDARD
        )
        
        assert result.is_valid is False
        assert "Hash mismatch" in result.error_message
    
    def test_verify_file_integrity_empty_hash(self, verifier, temp_file):
        """Test verification with empty expected hash"""
        file_path, test_data = temp_file
        
        result = verifier.verify_file_integrity(
            file_path, "", IntegrityLevel.STANDARD
        )
        
        # Should still pass basic checks but skip hash verification
        assert result.is_valid is True
        assert result.has_warnings()
        assert any("hash not provided" in warning.lower() for warning in result.warnings)
    
    def test_verify_file_integrity_large_file(self, verifier):
        """Test verification of file that's too large"""
        large_file = "/path/to/large/file.ts"
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=200 * 1024 * 1024):  # 200MB
            
            result = verifier.verify_file_integrity(large_file, "dummy_hash")
            
            assert result.is_valid is False
            assert "too large" in result.error_message.lower()
    
    def test_calculate_file_hash_md5(self, verifier, temp_file):
        """Test MD5 hash calculation"""
        file_path, test_data = temp_file
        expected_hash = hashlib.md5(test_data).hexdigest()
        
        calculated_hash = verifier._calculate_file_hash(file_path, "md5")
        
        assert calculated_hash == expected_hash
    
    def test_calculate_file_hash_sha256(self, verifier, temp_file):
        """Test SHA256 hash calculation"""
        file_path, test_data = temp_file
        expected_hash = hashlib.sha256(test_data).hexdigest()
        
        calculated_hash = verifier._calculate_file_hash(file_path, "sha256")
        
        assert calculated_hash == expected_hash
    
    def test_calculate_file_hash_invalid_algorithm(self, verifier, temp_file):
        """Test hash calculation with invalid algorithm"""
        file_path, test_data = temp_file
        
        with pytest.raises(ValueError):
            verifier._calculate_file_hash(file_path, "invalid_algorithm")
    
    def test_verify_multiple_hashes(self, verifier, temp_file):
        """Test verification with multiple hash algorithms"""
        file_path, test_data = temp_file
        
        result = verifier._verify_multiple_hashes(file_path)
        
        assert "md5" in result
        assert "sha1" in result
        assert "sha256" in result
        assert result["md5"] == hashlib.md5(test_data).hexdigest()
        assert result["sha256"] == hashlib.sha256(test_data).hexdigest()
    
    def test_verify_file_format_ts(self, verifier):
        """Test TS file format verification"""
        # Create a file with TS sync bytes
        fd, ts_file = tempfile.mkstemp(suffix=".ts")
        ts_data = b'\x47' + b'\x00' * 187  # Basic TS packet
        os.write(fd, ts_data * 5)  # Multiple packets
        os.close(fd)
        
        try:
            warnings = verifier._verify_file_format(ts_file)
            
            # Should have no warnings for valid TS format
            assert len(warnings) == 0
        finally:
            if os.path.exists(ts_file):
                os.unlink(ts_file)
    
    def test_verify_file_format_invalid_ts(self, verifier):
        """Test verification of invalid TS format"""
        # Create a file without proper TS structure
        fd, invalid_file = tempfile.mkstemp(suffix=".ts")
        invalid_data = b'\x00' * 1000  # No sync bytes
        os.write(fd, invalid_data)
        os.close(fd)
        
        try:
            warnings = verifier._verify_file_format(invalid_file)
            
            # Should have warnings for invalid TS format
            assert len(warnings) > 0
            assert any("sync byte" in warning.lower() for warning in warnings)
        finally:
            if os.path.exists(invalid_file):
                os.unlink(invalid_file)
    
    def test_verify_file_format_non_ts(self, verifier):
        """Test verification of non-TS file"""
        # Create a regular text file
        fd, text_file = tempfile.mkstemp(suffix=".txt")
        os.write(fd, b"This is not a TS file")
        os.close(fd)
        
        try:
            warnings = verifier._verify_file_format(text_file)
            
            # Should have warnings about file extension
            assert len(warnings) > 0
            assert any("extension" in warning.lower() for warning in warnings)
        finally:
            if os.path.exists(text_file):
                os.unlink(text_file)
    
    def test_get_verification_stats(self, verifier, temp_file):
        """Test getting verification statistics"""
        # Initially empty
        stats = verifier.get_verification_stats()
        assert stats["total_verifications"] == 0
        assert stats["successful_verifications"] == 0
        assert stats["failed_verifications"] == 0
        assert stats["success_rate"] == 1.0
        
        # Perform some verifications
        file_path, test_data = temp_file
        expected_hash = hashlib.md5(test_data).hexdigest()
        
        verifier.verify_file_integrity(file_path, expected_hash)
        verifier.verify_file_integrity("/nonexistent/file.ts", "dummy_hash")
        
        stats = verifier.get_verification_stats()
        assert stats["total_verifications"] == 2
        assert stats["successful_verifications"] == 1
        assert stats["failed_verifications"] == 1
        assert stats["success_rate"] == 0.5
    
    def test_reset_stats(self, verifier, temp_file):
        """Test resetting verification statistics"""
        # Perform some verifications
        file_path, test_data = temp_file
        expected_hash = hashlib.md5(test_data).hexdigest()
        
        verifier.verify_file_integrity(file_path, expected_hash)
        verifier.verify_file_integrity("/nonexistent/file.ts", "dummy_hash")
        
        # Stats should have data
        stats = verifier.get_verification_stats()
        assert stats["total_verifications"] == 2
        
        # Reset stats
        verifier.reset_stats()
        
        # Stats should be reset
        stats = verifier.get_verification_stats()
        assert stats["total_verifications"] == 0
        assert stats["successful_verifications"] == 0
        assert stats["failed_verifications"] == 0


class TestGlobalContentIntegrityVerifier:
    """Test global content integrity verifier instance"""
    
    def test_global_instance_exists(self):
        """Test that global instance exists and is properly initialized"""
        assert content_integrity_verifier is not None
        assert isinstance(content_integrity_verifier, ContentIntegrityVerifier)
    
    def test_global_instance_functionality(self):
        """Test basic functionality of global instance"""
        # Create a temporary test file
        fd, temp_file = tempfile.mkstemp(suffix=".ts")
        test_data = b"Test data for global verifier"
        os.write(fd, test_data)
        os.close(fd)
        
        try:
            # Should be able to verify file integrity
            expected_hash = hashlib.md5(test_data).hexdigest()
            result = content_integrity_verifier.verify_file_integrity(
                temp_file, expected_hash, IntegrityLevel.BASIC
            )
            assert isinstance(result, IntegrityResult)
            assert result.is_valid is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__])
