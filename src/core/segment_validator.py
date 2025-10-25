"""
Segment Validator for VidTanium

This module provides comprehensive validation for downloaded segments including
checksum verification, size validation, and format checking.
"""

import os
import hashlib
import mimetypes
import struct
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result enumeration"""
    VALID = "valid"
    INVALID_SIZE = "invalid_size"
    INVALID_CHECKSUM = "invalid_checksum"
    INVALID_FORMAT = "invalid_format"
    CORRUPTED = "corrupted"
    MISSING = "missing"
    UNKNOWN_ERROR = "unknown_error"


class HashAlgorithm(Enum):
    """Supported hash algorithms"""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"
    CRC32 = "crc32"


@dataclass
class ValidationConfig:
    """Configuration for segment validation"""
    enable_size_validation: bool = True
    enable_checksum_validation: bool = True
    enable_format_validation: bool = True
    enable_content_validation: bool = True
    hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    min_file_size: int = 1  # 1 byte
    allowed_mime_types: List[str] = field(default_factory=lambda: [
        'video/mp2t',  # MPEG-TS
        'video/mp4',
        'video/webm',
        'application/octet-stream'
    ])
    strict_validation: bool = False  # If True, any validation failure is fatal


@dataclass
class ValidationReport:
    """Detailed validation report for a segment"""
    segment_index: int
    file_path: str
    result: ValidationResult
    file_size: int = 0
    expected_size: Optional[int] = None
    calculated_checksum: str = ""
    expected_checksum: str = ""
    mime_type: str = ""
    validation_time: float = 0.0
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return self.result == ValidationResult.VALID
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0


class SegmentValidator:
    """Comprehensive segment validator"""
    
    def __init__(self, config: Optional[ValidationConfig] = None) -> None:
        self.config = config or ValidationConfig()
        self.validation_cache: Dict[str, ValidationReport] = {}
        
        # Performance tracking
        self.validation_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "total_validation_time": 0.0,
            "cache_hits": 0
        }
        
        logger.info("Segment validator initialized")
    
    def validate_segment(self, segment_index: int, file_path: str,
                        expected_size: Optional[int] = None,
                        expected_checksum: str = "",
                        force_revalidation: bool = False) -> ValidationReport:
        """Validate a downloaded segment comprehensively"""
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{file_path}_{os.path.getmtime(file_path) if os.path.exists(file_path) else 0}"
        if not force_revalidation and cache_key in self.validation_cache:
            self.validation_stats["cache_hits"] += 1
            return self.validation_cache[cache_key]
        
        report = ValidationReport(
            segment_index=segment_index,
            file_path=file_path,
            result=ValidationResult.VALID
        )
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                report.result = ValidationResult.MISSING
                report.error_message = f"Segment file not found: {file_path}"
                return report
            
            # Get file info
            report.file_size = os.path.getsize(file_path)
            report.expected_size = expected_size
            report.expected_checksum = expected_checksum
            
            # Perform validations
            if self.config.enable_size_validation:
                size_result = self._validate_size(report)
                if size_result != ValidationResult.VALID:
                    report.result = size_result
                    if self.config.strict_validation:
                        return report
            
            if self.config.enable_format_validation:
                format_result = self._validate_format(report)
                if format_result != ValidationResult.VALID:
                    if self.config.strict_validation:
                        report.result = format_result
                        return report
                    else:
                        report.warnings.append(f"Format validation warning: {format_result.value}")
            
            if self.config.enable_checksum_validation and expected_checksum:
                checksum_result = self._validate_checksum(report)
                if checksum_result != ValidationResult.VALID:
                    report.result = checksum_result
                    if self.config.strict_validation:
                        return report
            
            if self.config.enable_content_validation:
                content_result = self._validate_content(report)
                if content_result != ValidationResult.VALID:
                    if self.config.strict_validation:
                        report.result = content_result
                        return report
                    else:
                        report.warnings.append(f"Content validation warning: {content_result.value}")
            
            # If we get here, validation passed
            if report.result == ValidationResult.VALID or not self.config.strict_validation:
                report.result = ValidationResult.VALID
            
        except Exception as e:
            report.result = ValidationResult.UNKNOWN_ERROR
            report.error_message = f"Validation error: {str(e)}"
            logger.error(f"Error validating segment {segment_index}: {e}")
        
        finally:
            report.validation_time = time.time() - start_time
            
            # Update statistics
            self.validation_stats["total_validations"] += 1
            self.validation_stats["total_validation_time"] += report.validation_time
            
            if report.is_valid():
                self.validation_stats["successful_validations"] += 1
            else:
                self.validation_stats["failed_validations"] += 1
            
            # Cache result
            self.validation_cache[cache_key] = report
            
            logger.debug(f"Validated segment {segment_index}: {report.result.value} "
                        f"({report.validation_time:.3f}s)")
        
        return report
    
    def _validate_size(self, report: ValidationReport) -> ValidationResult:
        """Validate file size"""
        file_size = report.file_size
        
        # Check minimum size
        if file_size < self.config.min_file_size:
            report.error_message = f"File too small: {file_size} bytes (min: {self.config.min_file_size})"
            return ValidationResult.INVALID_SIZE
        
        # Check maximum size
        if file_size > self.config.max_file_size:
            report.error_message = f"File too large: {file_size} bytes (max: {self.config.max_file_size})"
            return ValidationResult.INVALID_SIZE
        
        # Check expected size if provided
        if report.expected_size is not None and file_size != report.expected_size:
            report.error_message = f"Size mismatch: got {file_size}, expected {report.expected_size}"
            return ValidationResult.INVALID_SIZE
        
        return ValidationResult.VALID
    
    def _validate_checksum(self, report: ValidationReport) -> ValidationResult:
        """Validate file checksum"""
        if not report.expected_checksum:
            return ValidationResult.VALID
        
        try:
            calculated_checksum = self._calculate_checksum(report.file_path)
            report.calculated_checksum = calculated_checksum
            
            if calculated_checksum.lower() != report.expected_checksum.lower():
                report.error_message = (f"Checksum mismatch: calculated {calculated_checksum}, "
                                      f"expected {report.expected_checksum}")
                return ValidationResult.INVALID_CHECKSUM
            
        except Exception as e:
            report.error_message = f"Checksum calculation failed: {str(e)}"
            return ValidationResult.UNKNOWN_ERROR
        
        return ValidationResult.VALID
    
    def _validate_format(self, report: ValidationReport) -> ValidationResult:
        """Validate file format"""
        try:
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(report.file_path)
            if not mime_type:
                # Try to detect from file content
                mime_type = self._detect_mime_type_from_content(report.file_path)
            
            report.mime_type = mime_type or "unknown"
            
            # Check if MIME type is allowed
            if (self.config.allowed_mime_types and 
                mime_type not in self.config.allowed_mime_types and
                "application/octet-stream" not in self.config.allowed_mime_types):
                report.error_message = f"Invalid file type: {mime_type}"
                return ValidationResult.INVALID_FORMAT
            
        except Exception as e:
            report.error_message = f"Format validation failed: {str(e)}"
            return ValidationResult.UNKNOWN_ERROR
        
        return ValidationResult.VALID
    
    def _validate_content(self, report: ValidationReport) -> ValidationResult:
        """Validate file content structure"""
        try:
            # Basic content validation - check if file is readable and not corrupted
            with open(report.file_path, 'rb') as f:
                # Read first few bytes to check file header
                header = f.read(16)
                
                if len(header) == 0:
                    report.error_message = "File is empty"
                    return ValidationResult.CORRUPTED
                
                # Check for common video file signatures
                if self._is_video_file_header(header):
                    # Additional video-specific validation could go here
                    pass
                
                # Try to read the entire file to check for corruption
                # (This is expensive, so only do it for smaller files)
                if report.file_size < 10 * 1024 * 1024:  # 10MB
                    f.seek(0)
                    try:
                        while True:
                            chunk = f.read(8192)
                            if not chunk:
                                break
                    except Exception as e:
                        report.error_message = f"File appears corrupted: {str(e)}"
                        return ValidationResult.CORRUPTED
            
        except Exception as e:
            report.error_message = f"Content validation failed: {str(e)}"
            return ValidationResult.UNKNOWN_ERROR
        
        return ValidationResult.VALID
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum using configured algorithm"""
        if self.config.hash_algorithm == HashAlgorithm.CRC32:
            import zlib
            crc = 0
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    crc = zlib.crc32(chunk, crc)
            return format(crc & 0xffffffff, '08x')

        # Handle hash-based algorithms
        if self.config.hash_algorithm == HashAlgorithm.MD5:
            hasher = hashlib.md5()
        elif self.config.hash_algorithm == HashAlgorithm.SHA1:
            hasher = hashlib.sha1()
        elif self.config.hash_algorithm == HashAlgorithm.SHA512:
            hasher = hashlib.sha512()
        else:  # SHA256 or any other value
            hasher = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        return hasher.hexdigest()
    
    def _detect_mime_type_from_content(self, file_path: str) -> Optional[str]:
        """Detect MIME type from file content"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
                
                # MPEG-TS files typically start with 0x47
                if header[0:1] == b'\x47':
                    return 'video/mp2t'
                
                # MP4 files have 'ftyp' at offset 4
                if len(header) >= 8 and header[4:8] == b'ftyp':
                    return 'video/mp4'
                
                # WebM files start with EBML header
                if header.startswith(b'\x1a\x45\xdf\xa3'):
                    return 'video/webm'
                
        except Exception:
            pass
        
        return None
    
    def _is_video_file_header(self, header: bytes) -> bool:
        """Check if header indicates a video file"""
        if len(header) < 4:
            return False
        
        # Common video file signatures
        video_signatures = [
            b'\x47',  # MPEG-TS
            b'\x00\x00\x00\x18ftyp',  # MP4 (partial)
            b'\x00\x00\x00\x20ftyp',  # MP4 (partial)
            b'\x1a\x45\xdf\xa3',  # WebM/Matroska
        ]
        
        for signature in video_signatures:
            if header.startswith(signature):
                return True
        
        return False
    
    def validate_batch(self, segments: List[Tuple[int, str, Optional[int], str]]) -> List[ValidationReport]:
        """Validate multiple segments in batch"""
        reports = []
        
        for segment_index, file_path, expected_size, expected_checksum in segments:
            report = self.validate_segment(segment_index, file_path, expected_size, expected_checksum)
            reports.append(report)
        
        return reports
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        stats = self.validation_stats.copy()
        
        if stats["total_validations"] > 0:
            stats["success_rate"] = stats["successful_validations"] / stats["total_validations"]
            stats["average_validation_time"] = stats["total_validation_time"] / stats["total_validations"]
        else:
            stats["success_rate"] = 0.0
            stats["average_validation_time"] = 0.0
        
        stats["cache_size"] = len(self.validation_cache)
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear validation cache"""
        self.validation_cache.clear()
        logger.debug("Validation cache cleared")
    
    def cleanup_cache(self, max_age_seconds: float = 3600.0) -> None:
        """Clean up old cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, report in self.validation_cache.items():
            if current_time - report.validation_time > max_age_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.validation_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global segment validator instance
segment_validator = SegmentValidator()
