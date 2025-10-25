"""
Tests for segment validation
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from src.core.segment_validator import (
    SegmentValidator, ValidationResult, segment_validator
)


class TestValidationResult:
    """Test ValidationResult dataclass"""
    
    def test_validation_result_valid(self) -> None:
        """Test ValidationResult for valid segment"""
        result = ValidationResult(
            segment_id=5,
            is_valid=True,
            file_size=1024,
            expected_size=1024,
            warnings=[],
            error_message=""
        )
        
        assert result.segment_id == 5
        assert result.is_valid is True
        assert result.file_size == 1024
        assert result.expected_size == 1024
        assert result.warnings == []
        assert result.error_message == ""
        assert result.validation_time > 0
    
    def test_validation_result_invalid(self) -> None:
        """Test ValidationResult for invalid segment"""
        result = ValidationResult(
            segment_id=3,
            is_valid=False,
            file_size=512,
            expected_size=1024,
            warnings=["Size mismatch"],
            error_message="File size does not match expected size"
        )
        
        assert result.segment_id == 3
        assert result.is_valid is False
        assert result.file_size == 512
        assert result.expected_size == 1024
        assert "Size mismatch" in result.warnings
        assert "File size does not match expected size" in result.error_message
    
    def test_has_warnings(self) -> None:
        """Test has_warnings method"""
        result_no_warnings = ValidationResult(
            segment_id=1, is_valid=True, file_size=1024, expected_size=1024,
            warnings=[], error_message=""
        )
        
        result_with_warnings = ValidationResult(
            segment_id=2, is_valid=True, file_size=1024, expected_size=1000,
            warnings=["Minor size difference"], error_message=""
        )
        
        assert not result_no_warnings.has_warnings()
        assert result_with_warnings.has_warnings()


class TestSegmentValidator:
    """Test SegmentValidator class"""
    
    @pytest.fixture
    def temp_file(self) -> None:
        """Create a temporary file for testing"""
        fd, path = tempfile.mkstemp(suffix=".ts")
        # Write some test data
        test_data = b"Test segment data for validation"
        os.write(fd, test_data)
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def validator(self) -> None:
        """Create a fresh SegmentValidator for testing"""
        return SegmentValidator()
    
    def test_initialization(self, validator) -> None:
        """Test SegmentValidator initialization"""
        assert validator.validation_stats == {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "warnings_count": 0
        }
        assert validator.min_segment_size == 1024  # 1KB
        assert validator.max_segment_size == 10 * 1024 * 1024  # 10MB
        assert validator.size_tolerance == 0.1  # 10%
    
    def test_validate_segment_file_exists(self, validator, temp_file) -> None:
        """Test validating existing segment file"""
        segment_id = 5
        expected_size = os.path.getsize(temp_file)
        
        result = validator.validate_segment(segment_id, temp_file, expected_size)
        
        assert isinstance(result, ValidationResult)
        assert result.segment_id == segment_id
        assert result.is_valid is True
        assert result.file_size == expected_size
        assert result.expected_size == expected_size
        assert result.error_message == ""
    
    def test_validate_segment_file_not_exists(self, validator) -> None:
        """Test validating non-existent segment file"""
        segment_id = 3
        nonexistent_file = "/path/to/nonexistent/file.ts"
        
        result = validator.validate_segment(segment_id, nonexistent_file, 1024)
        
        assert result.segment_id == segment_id
        assert result.is_valid is False
        assert "File does not exist" in result.error_message
    
    def test_validate_segment_empty_file(self, validator) -> None:
        """Test validating empty segment file"""
        fd, empty_file = tempfile.mkstemp(suffix=".ts")
        os.close(fd)  # Create empty file
        
        try:
            segment_id = 1
            result = validator.validate_segment(segment_id, empty_file, 1024)
            
            assert result.segment_id == segment_id
            assert result.is_valid is False
            assert "File is empty" in result.error_message
        finally:
            if os.path.exists(empty_file):
                os.unlink(empty_file)
    
    def test_validate_segment_size_mismatch_major(self, validator, temp_file) -> None:
        """Test validating segment with major size mismatch"""
        segment_id = 2
        actual_size = os.path.getsize(temp_file)
        expected_size = actual_size * 3  # 3x larger than actual
        
        result = validator.validate_segment(segment_id, temp_file, expected_size)
        
        assert result.segment_id == segment_id
        assert result.is_valid is False
        assert "Size mismatch" in result.error_message
        assert result.file_size == actual_size
        assert result.expected_size == expected_size
    
    def test_validate_segment_size_mismatch_minor(self, validator, temp_file) -> None:
        """Test validating segment with minor size mismatch (within tolerance)"""
        segment_id = 4
        actual_size = os.path.getsize(temp_file)
        expected_size = int(actual_size * 1.05)  # 5% larger (within 10% tolerance)
        
        result = validator.validate_segment(segment_id, temp_file, expected_size)
        
        assert result.segment_id == segment_id
        assert result.is_valid is True  # Should be valid due to tolerance
        assert result.has_warnings()  # But should have warnings
        assert "size difference" in result.warnings[0].lower()
    
    def test_validate_segment_too_small(self, validator) -> None:
        """Test validating segment that's too small"""
        fd, small_file = tempfile.mkstemp(suffix=".ts")
        os.write(fd, b"tiny")  # Very small file
        os.close(fd)
        
        try:
            segment_id = 6
            result = validator.validate_segment(segment_id, small_file, 100)
            
            assert result.segment_id == segment_id
            assert result.is_valid is False
            assert "too small" in result.error_message.lower()
        finally:
            if os.path.exists(small_file):
                os.unlink(small_file)
    
    def test_validate_segment_too_large(self, validator) -> None:
        """Test validating segment that's too large"""
        # Mock a very large file
        large_file = "/path/to/large/file.ts"
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=20 * 1024 * 1024):  # 20MB
            
            segment_id = 7
            result = validator.validate_segment(segment_id, large_file, 20 * 1024 * 1024)
            
            assert result.segment_id == segment_id
            assert result.is_valid is False
            assert "too large" in result.error_message.lower()
    
    def test_validate_segment_content_basic(self, validator, temp_file) -> None:
        """Test basic content validation"""
        segment_id = 8
        expected_size = os.path.getsize(temp_file)
        
        result = validator.validate_segment(segment_id, temp_file, expected_size)
        
        # Should pass basic validation
        assert result.is_valid is True
    
    def test_validate_segment_content_ts_format(self, validator) -> None:
        """Test TS format validation"""
        # Create a file with TS sync byte
        fd, ts_file = tempfile.mkstemp(suffix=".ts")
        # TS packets start with sync byte 0x47
        ts_data = b'\x47' + b'\x00' * 187  # Basic TS packet structure
        os.write(fd, ts_data * 10)  # Multiple packets
        os.close(fd)
        
        try:
            segment_id = 9
            result = validator.validate_segment(segment_id, ts_file, len(ts_data) * 10)
            
            assert result.is_valid is True
        finally:
            if os.path.exists(ts_file):
                os.unlink(ts_file)
    
    def test_validate_segment_content_invalid_ts(self, validator) -> None:
        """Test validation of invalid TS format"""
        # Create a file without proper TS sync bytes
        fd, invalid_ts_file = tempfile.mkstemp(suffix=".ts")
        invalid_data = b'\x00' * 1000  # No sync bytes
        os.write(fd, invalid_data)
        os.close(fd)
        
        try:
            segment_id = 10
            result = validator.validate_segment(segment_id, invalid_ts_file, 1000)
            
            # Should have warnings about TS format
            assert result.has_warnings() or not result.is_valid
        finally:
            if os.path.exists(invalid_ts_file):
                os.unlink(invalid_ts_file)
    
    def test_get_validation_stats(self, validator, temp_file) -> None:
        """Test getting validation statistics"""
        # Initially empty
        stats = validator.get_validation_stats()
        assert stats["total_validations"] == 0
        assert stats["successful_validations"] == 0
        assert stats["failed_validations"] == 0
        assert stats["success_rate"] == 1.0
        
        # Perform some validations
        validator.validate_segment(1, temp_file, os.path.getsize(temp_file))
        validator.validate_segment(2, "/nonexistent/file.ts", 1024)
        
        stats = validator.get_validation_stats()
        assert stats["total_validations"] == 2
        assert stats["successful_validations"] == 1
        assert stats["failed_validations"] == 1
        assert stats["success_rate"] == 0.5
    
    def test_reset_stats(self, validator, temp_file) -> None:
        """Test resetting validation statistics"""
        # Perform some validations
        validator.validate_segment(1, temp_file, os.path.getsize(temp_file))
        validator.validate_segment(2, "/nonexistent/file.ts", 1024)
        
        # Stats should have data
        stats = validator.get_validation_stats()
        assert stats["total_validations"] == 2
        
        # Reset stats
        validator.reset_stats()
        
        # Stats should be reset
        stats = validator.get_validation_stats()
        assert stats["total_validations"] == 0
        assert stats["successful_validations"] == 0
        assert stats["failed_validations"] == 0
    
    def test_is_size_within_tolerance(self, validator) -> None:
        """Test size tolerance checking"""
        # Exact match
        assert validator._is_size_within_tolerance(1000, 1000) is True
        
        # Within tolerance (10%)
        assert validator._is_size_within_tolerance(1000, 1050) is True  # 5% difference
        assert validator._is_size_within_tolerance(1000, 950) is True   # 5% difference
        
        # Outside tolerance
        assert validator._is_size_within_tolerance(1000, 1200) is False  # 20% difference
        assert validator._is_size_within_tolerance(1000, 800) is False   # 20% difference
    
    def test_validate_ts_format_valid(self, validator) -> None:
        """Test TS format validation with valid data"""
        # Create valid TS data with sync bytes
        ts_data = b'\x47' + b'\x00' * 187  # Basic TS packet
        ts_data += b'\x47' + b'\x01' * 187  # Another packet
        
        warnings = validator._validate_ts_format(ts_data)
        
        # Should have no warnings for valid TS data
        assert len(warnings) == 0
    
    def test_validate_ts_format_invalid(self, validator) -> None:
        """Test TS format validation with invalid data"""
        # Create invalid data without sync bytes
        invalid_data = b'\x00' * 1000
        
        warnings = validator._validate_ts_format(invalid_data)
        
        # Should have warnings for invalid TS data
        assert len(warnings) > 0
        assert any("sync byte" in warning.lower() for warning in warnings)


class TestGlobalSegmentValidator:
    """Test global segment validator instance"""
    
    def test_global_instance_exists(self) -> None:
        """Test that global instance exists and is properly initialized"""
        assert segment_validator is not None
        assert isinstance(segment_validator, SegmentValidator)
    
    def test_global_instance_functionality(self) -> None:
        """Test basic functionality of global instance"""
        # Create a temporary test file
        fd, temp_file = tempfile.mkstemp(suffix=".ts")
        test_data = b"Test data for global validator"
        os.write(fd, test_data)
        os.close(fd)
        
        try:
            # Should be able to validate segments
            result = segment_validator.validate_segment(1, temp_file, len(test_data))
            assert isinstance(result, ValidationResult)
            assert result.is_valid is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__])
