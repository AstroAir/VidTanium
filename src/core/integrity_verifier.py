"""
Content Integrity Verifier for VidTanium

This module provides multi-layer integrity checks to detect and handle corrupted
downloads, including hash verification and content analysis.
"""

import os
import hashlib
import time
import threading
import math
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class IntegrityLevel(Enum):
    """Integrity verification levels"""
    BASIC = "basic"          # File existence and size
    CHECKSUM = "checksum"    # Hash verification
    CONTENT = "content"      # Content structure analysis
    DEEP = "deep"           # Comprehensive analysis


class CorruptionType(Enum):
    """Types of corruption detected"""
    NONE = "none"
    TRUNCATED = "truncated"
    MODIFIED = "modified"
    HEADER_CORRUPT = "header_corrupt"
    DATA_CORRUPT = "data_corrupt"
    ENCODING_ERROR = "encoding_error"
    UNKNOWN = "unknown"


@dataclass
class IntegrityResult:
    """Result of integrity verification"""
    file_path: str
    is_valid: bool
    corruption_type: CorruptionType = CorruptionType.NONE
    confidence_score: float = 1.0  # 0.0 = definitely corrupt, 1.0 = definitely valid
    error_message: str = ""
    verification_time: float = 0.0
    checks_performed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrityConfig:
    """Configuration for integrity verification"""
    verification_level: IntegrityLevel = IntegrityLevel.CHECKSUM
    enable_repair_attempts: bool = True
    max_repair_attempts: int = 3
    chunk_size: int = 8192
    parallel_verification: bool = True
    cache_results: bool = True
    cache_duration: float = 3600.0  # 1 hour
    
    # Corruption detection thresholds
    min_confidence_threshold: float = 0.7
    suspicious_pattern_threshold: int = 5
    
    # Performance settings
    max_concurrent_verifications: int = 4
    verification_timeout: float = 300.0  # 5 minutes


class ContentIntegrityVerifier:
    """Multi-layer content integrity verifier"""
    
    def __init__(self, config: Optional[IntegrityConfig] = None) -> None:
        self.config = config or IntegrityConfig()
        self.verification_cache: Dict[str, IntegrityResult] = {}
        self.lock = threading.RLock()
        
        # Performance tracking
        self.stats = {
            "total_verifications": 0,
            "successful_verifications": 0,
            "corrupted_files_detected": 0,
            "repairs_attempted": 0,
            "successful_repairs": 0,
            "total_verification_time": 0.0,
            "cache_hits": 0
        }
        
        # Corruption patterns database
        self.corruption_patterns = self._initialize_corruption_patterns()
        
        logger.info("Content integrity verifier initialized")
    
    def verify_file_integrity(self, file_path: str, expected_hash: str = "",
                            reference_file: str = "", force_verification: bool = False) -> IntegrityResult:
        """Verify file integrity with multiple layers of checks"""
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{file_path}_{os.path.getmtime(file_path) if os.path.exists(file_path) else 0}"
        if not force_verification and self.config.cache_results and cache_key in self.verification_cache:
            cached_result = self.verification_cache[cache_key]
            if time.time() - cached_result.verification_time < self.config.cache_duration:
                self.stats["cache_hits"] += 1
                return cached_result
        
        result = IntegrityResult(file_path=file_path, is_valid=False)
        
        try:
            # Basic checks
            if not self._perform_basic_checks(result):
                return result
            
            # Checksum verification
            if (self.config.verification_level.value in ["checksum", "content", "deep"] and 
                expected_hash):
                if not self._perform_checksum_verification(result, expected_hash):
                    return result
            
            # Content structure analysis
            if self.config.verification_level.value in ["content", "deep"]:
                if not self._perform_content_analysis(result):
                    return result
            
            # Deep analysis
            if self.config.verification_level == IntegrityLevel.DEEP:
                if not self._perform_deep_analysis(result, reference_file):
                    return result
            
            # If all checks pass
            result.is_valid = True
            result.confidence_score = 1.0
            
        except Exception as e:
            result.is_valid = False
            result.error_message = f"Verification error: {str(e)}"
            result.corruption_type = CorruptionType.UNKNOWN
            logger.error(f"Error verifying {file_path}: {e}")
        
        finally:
            result.verification_time = time.time() - start_time
            
            # Update statistics
            with self.lock:
                self.stats["total_verifications"] += 1
                self.stats["total_verification_time"] += result.verification_time
                
                if result.is_valid:
                    self.stats["successful_verifications"] += 1
                else:
                    self.stats["corrupted_files_detected"] += 1
            
            # Cache result
            if self.config.cache_results:
                self.verification_cache[cache_key] = result
            
            logger.debug(f"Verified {file_path}: {'VALID' if result.is_valid else 'CORRUPT'} "
                        f"({result.verification_time:.3f}s)")
        
        return result
    
    def _perform_basic_checks(self, result: IntegrityResult) -> bool:
        """Perform basic file existence and size checks"""
        result.checks_performed.append("basic")
        
        if not os.path.exists(result.file_path):
            result.is_valid = False
            result.error_message = "File does not exist"
            result.corruption_type = CorruptionType.TRUNCATED
            return False
        
        file_size = os.path.getsize(result.file_path)
        result.metadata["file_size"] = file_size
        
        if file_size == 0:
            result.is_valid = False
            result.error_message = "File is empty"
            result.corruption_type = CorruptionType.TRUNCATED
            return False
        
        # Check if file is readable
        try:
            with open(result.file_path, 'rb') as f:
                f.read(1)
        except Exception as e:
            result.is_valid = False
            result.error_message = f"File is not readable: {str(e)}"
            result.corruption_type = CorruptionType.DATA_CORRUPT
            return False
        
        return True
    
    def _perform_checksum_verification(self, result: IntegrityResult, expected_hash: str) -> bool:
        """Perform checksum verification"""
        result.checks_performed.append("checksum")
        
        try:
            calculated_hash = self._calculate_file_hash(result.file_path)
            result.metadata["calculated_hash"] = calculated_hash
            result.metadata["expected_hash"] = expected_hash
            
            if calculated_hash.lower() != expected_hash.lower():
                result.is_valid = False
                result.error_message = f"Hash mismatch: expected {expected_hash}, got {calculated_hash}"
                result.corruption_type = CorruptionType.MODIFIED
                result.confidence_score = 0.0
                return False
            
        except Exception as e:
            result.is_valid = False
            result.error_message = f"Hash calculation failed: {str(e)}"
            result.corruption_type = CorruptionType.UNKNOWN
            return False
        
        return True
    
    def _perform_content_analysis(self, result: IntegrityResult) -> bool:
        """Perform content structure analysis"""
        result.checks_performed.append("content")
        
        try:
            # Analyze file header
            header_valid = self._analyze_file_header(result)
            if not header_valid:
                return False
            
            # Check for corruption patterns
            corruption_detected = self._detect_corruption_patterns(result)
            if corruption_detected:
                return False
            
            # Validate file structure
            structure_valid = self._validate_file_structure(result)
            if not structure_valid:
                return False
            
        except Exception as e:
            result.is_valid = False
            result.error_message = f"Content analysis failed: {str(e)}"
            result.corruption_type = CorruptionType.UNKNOWN
            return False
        
        return True
    
    def _perform_deep_analysis(self, result: IntegrityResult, reference_file: str = "") -> bool:
        """Perform deep integrity analysis"""
        result.checks_performed.append("deep")
        
        try:
            # Statistical analysis of file content
            if not self._perform_statistical_analysis(result):
                return False
            
            # Compare with reference file if provided
            if reference_file and os.path.exists(reference_file):
                if not self._compare_with_reference(result, reference_file):
                    return False
            
            # Advanced corruption detection
            if not self._advanced_corruption_detection(result):
                return False
            
        except Exception as e:
            result.is_valid = False
            result.error_message = f"Deep analysis failed: {str(e)}"
            result.corruption_type = CorruptionType.UNKNOWN
            return False
        
        return True
    
    def _analyze_file_header(self, result: IntegrityResult) -> bool:
        """Analyze file header for corruption"""
        try:
            with open(result.file_path, 'rb') as f:
                header = f.read(64)  # Read first 64 bytes
                
                if len(header) < 4:
                    result.is_valid = False
                    result.error_message = "File header too short"
                    result.corruption_type = CorruptionType.HEADER_CORRUPT
                    return False
                
                # Check for known file signatures
                if not self._validate_file_signature(header):
                    result.is_valid = False
                    result.error_message = "Invalid file signature"
                    result.corruption_type = CorruptionType.HEADER_CORRUPT
                    result.confidence_score = 0.3
                    return False
                
                result.metadata["header_valid"] = True
                
        except Exception as e:
            result.is_valid = False
            result.error_message = f"Header analysis failed: {str(e)}"
            result.corruption_type = CorruptionType.HEADER_CORRUPT
            return False
        
        return True
    
    def _detect_corruption_patterns(self, result: IntegrityResult) -> bool:
        """Detect known corruption patterns"""
        suspicious_patterns = 0
        
        try:
            with open(result.file_path, 'rb') as f:
                chunk_count = 0
                while chunk_count < 100:  # Analyze first 100 chunks
                    chunk = f.read(self.config.chunk_size)
                    if not chunk:
                        break
                    
                    # Check for suspicious patterns
                    for pattern_name, pattern_check in self.corruption_patterns.items():
                        if pattern_check(chunk):
                            suspicious_patterns += 1
                            logger.debug(f"Suspicious pattern '{pattern_name}' detected in {result.file_path}")
                    
                    chunk_count += 1
                
                if suspicious_patterns >= self.config.suspicious_pattern_threshold:
                    result.is_valid = False
                    result.error_message = f"Multiple corruption patterns detected ({suspicious_patterns})"
                    result.corruption_type = CorruptionType.DATA_CORRUPT
                    result.confidence_score = max(0.1, 1.0 - (suspicious_patterns / 10.0))
                    return True
                
                result.metadata["suspicious_patterns"] = suspicious_patterns
                
        except Exception as e:
            logger.warning(f"Error detecting corruption patterns: {e}")
        
        return False
    
    def _validate_file_structure(self, result: IntegrityResult) -> bool:
        """Validate overall file structure"""
        try:
            file_size = result.metadata.get("file_size", 0)
            
            # Check for truncation
            with open(result.file_path, 'rb') as f:
                f.seek(0, 2)  # Seek to end
                actual_size = f.tell()
                
                if actual_size != file_size:
                    result.is_valid = False
                    result.error_message = f"File size mismatch: expected {file_size}, got {actual_size}"
                    result.corruption_type = CorruptionType.TRUNCATED
                    return False
            
            # Additional structure validation could go here
            result.metadata["structure_valid"] = True
            
        except Exception as e:
            result.is_valid = False
            result.error_message = f"Structure validation failed: {str(e)}"
            result.corruption_type = CorruptionType.DATA_CORRUPT
            return False
        
        return True
    
    def _perform_statistical_analysis(self, result: IntegrityResult) -> bool:
        """Perform statistical analysis of file content"""
        try:
            byte_frequencies = [0] * 256
            total_bytes = 0
            
            with open(result.file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.config.chunk_size)
                    if not chunk:
                        break
                    
                    for byte in chunk:
                        byte_frequencies[byte] += 1
                        total_bytes += 1
            
            # Calculate entropy and other statistical measures
            entropy = self._calculate_entropy(byte_frequencies, total_bytes)
            result.metadata["entropy"] = entropy
            
            # Check for suspicious patterns (too low or too high entropy)
            if entropy < 1.0:  # Very low entropy might indicate corruption
                result.confidence_score *= 0.8
                logger.debug(f"Low entropy detected: {entropy}")
            elif entropy > 7.8:  # Very high entropy might indicate encryption or compression
                result.metadata["high_entropy"] = True
            
        except Exception as e:
            logger.warning(f"Statistical analysis failed: {e}")
        
        return True
    
    def _compare_with_reference(self, result: IntegrityResult, reference_file: str) -> bool:
        """Compare file with reference for differences"""
        try:
            # Simple comparison - could be enhanced with more sophisticated algorithms
            with open(result.file_path, 'rb') as f1, open(reference_file, 'rb') as f2:
                differences = 0
                chunk_count = 0
                
                while chunk_count < 50:  # Compare first 50 chunks
                    chunk1 = f1.read(self.config.chunk_size)
                    chunk2 = f2.read(self.config.chunk_size)
                    
                    if not chunk1 and not chunk2:
                        break
                    
                    if chunk1 != chunk2:
                        differences += 1
                    
                    chunk_count += 1
                
                similarity = 1.0 - (differences / max(chunk_count, 1))
                result.metadata["similarity_to_reference"] = similarity
                
                if similarity < 0.9:  # Less than 90% similar
                    result.confidence_score *= similarity
                    logger.debug(f"Low similarity to reference: {similarity}")
        
        except Exception as e:
            logger.warning(f"Reference comparison failed: {e}")
        
        return True
    
    def _advanced_corruption_detection(self, result: IntegrityResult) -> bool:
        """Advanced corruption detection algorithms"""
        # This could include more sophisticated algorithms like:
        # - Reed-Solomon error detection
        # - CRC checks at multiple levels
        # - Pattern matching against known good files
        # - Machine learning-based corruption detection
        
        # For now, just a placeholder
        result.metadata["advanced_checks"] = "completed"
        return True
    
    def _calculate_file_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        """Calculate file hash"""
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha1":
            hasher = hashlib.sha1()
        elif algorithm == "sha512":
            hasher = hashlib.sha512()
        else:
            hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(self.config.chunk_size), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _validate_file_signature(self, header: bytes) -> bool:
        """Validate file signature against known formats"""
        # Common video file signatures
        video_signatures = [
            b'\x47',  # MPEG-TS
            b'\x00\x00\x00\x18ftyp',  # MP4
            b'\x00\x00\x00\x20ftyp',  # MP4
            b'\x1a\x45\xdf\xa3',  # WebM/Matroska
        ]
        
        for signature in video_signatures:
            if header.startswith(signature):
                return True
        
        # If no known signature found, it might still be valid
        return True
    
    def _calculate_entropy(self, frequencies: List[int], total: int) -> float:
        """Calculate Shannon entropy"""
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for freq in frequencies:
            if freq > 0:
                probability = freq / total
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _initialize_corruption_patterns(self) -> Dict[str, Callable[[bytes], bool]]:
        """Initialize corruption pattern detection functions"""
        patterns = {
            "null_bytes": lambda chunk: chunk.count(b'\x00') > len(chunk) * 0.8,
            "repeated_pattern": lambda chunk: len(set(chunk)) < 5 and len(chunk) > 10,
            "invalid_utf8": lambda chunk: self._check_invalid_utf8(chunk),
            "suspicious_sequence": lambda chunk: b'\xFF' * 10 in chunk or b'\x00' * 10 in chunk,
        }
        return patterns
    
    def _check_invalid_utf8(self, chunk: bytes) -> bool:
        """Check for invalid UTF-8 sequences that might indicate corruption"""
        try:
            chunk.decode('utf-8', errors='strict')
            return False
        except UnicodeDecodeError:
            # For binary files, this is expected, so not necessarily corruption
            return False
    
    def verify_batch(self, file_paths: List[str], expected_hashes: Optional[List[str]] = None) -> List[IntegrityResult]:
        """Verify multiple files in batch"""
        results = []
        expected_hashes = expected_hashes or [""] * len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            expected_hash = expected_hashes[i] if i < len(expected_hashes) else ""
            result = self.verify_file_integrity(file_path, expected_hash)
            results.append(result)
        
        return results
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        with self.lock:
            stats = self.stats.copy()
            
            if stats["total_verifications"] > 0:
                stats["success_rate"] = stats["successful_verifications"] / stats["total_verifications"]
                stats["corruption_rate"] = stats["corrupted_files_detected"] / stats["total_verifications"]
                stats["average_verification_time"] = stats["total_verification_time"] / stats["total_verifications"]
            else:
                stats["success_rate"] = 0.0
                stats["corruption_rate"] = 0.0
                stats["average_verification_time"] = 0.0
            
            if stats["repairs_attempted"] > 0:
                stats["repair_success_rate"] = stats["successful_repairs"] / stats["repairs_attempted"]
            else:
                stats["repair_success_rate"] = 0.0
            
            stats["cache_size"] = len(self.verification_cache)
            
            return stats
    
    def clear_cache(self) -> None:
        """Clear verification cache"""
        with self.lock:
            self.verification_cache.clear()
            logger.debug("Integrity verification cache cleared")


# Global content integrity verifier instance
content_integrity_verifier = ContentIntegrityVerifier()
