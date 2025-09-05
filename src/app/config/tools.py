"""
Configuration Management Tools

Provides utilities for configuration export/import, validation, 
backup/restore, and other management operations.
"""

import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from .schema import ConfigurationSchema, ConfigurationValidator, ValidationLevel
from .presets import PresetManager
from .feature_flags import FeatureFlagManager


@dataclass
class ConfigurationDiff:
    """Represents differences between configurations"""
    added: Dict[str, Any]
    removed: Dict[str, Any]
    modified: Dict[str, Tuple[Any, Any]]  # old_value, new_value
    unchanged: Dict[str, Any]


@dataclass
class BackupInfo:
    """Information about a configuration backup"""
    path: Path
    timestamp: datetime
    version: str
    description: str
    size_bytes: int


class ConfigurationTools:
    """Configuration management utilities"""
    
    def __init__(self, 
                 schema: ConfigurationSchema,
                 preset_manager: Optional[PresetManager] = None,
                 feature_manager: Optional[FeatureFlagManager] = None):
        self.schema = schema
        self.validator = ConfigurationValidator(schema)
        self.preset_manager = preset_manager
        self.feature_manager = feature_manager
    
    def validate_configuration(self, 
                             config: Dict[str, Any], 
                             validation_level: ValidationLevel = ValidationLevel.NORMAL) -> Tuple[bool, List[str], List[str]]:
        """
        Validate configuration with detailed reporting
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        validator = ConfigurationValidator(self.schema, validation_level)
        return validator.validate(config)
    
    def export_configuration(self, 
                           config: Dict[str, Any], 
                           output_path: Path,
                           format: str = "json",
                           include_metadata: bool = True) -> bool:
        """
        Export configuration to file
        
        Args:
            config: Configuration to export
            output_path: Output file path
            format: Export format (json, yaml)
            include_metadata: Include metadata in export
            
        Returns:
            Success status
        """
        try:
            export_data = config.copy()
            
            if include_metadata:
                export_data["_metadata"] = {
                    "exported_at": datetime.now().isoformat(),
                    "schema_version": self.schema.schema_version,
                    "exported_by": "VidTanium Configuration Tools"
                }
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if format.lower() == "yaml":
                    yaml.dump(export_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_configuration(self, 
                           input_path: Path,
                           validate: bool = True) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Import configuration from file
        
        Args:
            input_path: Input file path
            validate: Whether to validate imported configuration
            
        Returns:
            Tuple of (success, config_data, errors)
        """
        errors = []
        
        try:
            if not input_path.exists():
                errors.append(f"Configuration file not found: {input_path}")
                return False, None, errors
            
            with open(input_path, 'r', encoding='utf-8') as f:
                if input_path.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            # Remove metadata if present
            if "_metadata" in config:
                del config["_metadata"]
            
            # Validate if requested
            if validate:
                is_valid, validation_errors, warnings = self.validate_configuration(config)
                if not is_valid:
                    errors.extend(validation_errors)
                    return False, config, errors
                
                if warnings:
                    logger.warning(f"Configuration import warnings: {'; '.join(warnings)}")
            
            logger.info(f"Configuration imported from {input_path}")
            return True, config, errors
            
        except Exception as e:
            errors.append(f"Failed to import configuration: {e}")
            logger.error(f"Failed to import configuration from {input_path}: {e}")
            return False, None, errors
    
    def create_backup(self, 
                     config: Dict[str, Any], 
                     backup_dir: Path,
                     description: str = "") -> Optional[BackupInfo]:
        """
        Create configuration backup
        
        Args:
            config: Configuration to backup
            backup_dir: Backup directory
            description: Backup description
            
        Returns:
            BackupInfo if successful, None otherwise
        """
        try:
            # Ensure backup directory exists
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp_str}.json"
            backup_path = backup_dir / backup_filename
            
            # Add backup metadata
            backup_data = config.copy()
            backup_data["_backup_metadata"] = {
                "created_at": timestamp.isoformat(),
                "description": description,
                "schema_version": self.schema.schema_version
            }
            
            # Write backup file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Get file size
            size_bytes = backup_path.stat().st_size
            
            backup_info = BackupInfo(
                path=backup_path,
                timestamp=timestamp,
                version=self.schema.schema_version,
                description=description,
                size_bytes=size_bytes
            )
            
            logger.info(f"Configuration backup created: {backup_path}")
            return backup_info
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def list_backups(self, backup_dir: Path) -> List[BackupInfo]:
        """List available configuration backups"""
        backups: List[BackupInfo] = []
        
        if not backup_dir.exists():
            return backups
        
        backup_files = list(backup_dir.glob("config_backup_*.json"))
        
        for backup_file in backup_files:
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                metadata = backup_data.get("_backup_metadata", {})
                
                backup_info = BackupInfo(
                    path=backup_file,
                    timestamp=datetime.fromisoformat(metadata.get("created_at", "1970-01-01T00:00:00")),
                    version=metadata.get("schema_version", "unknown"),
                    description=metadata.get("description", ""),
                    size_bytes=backup_file.stat().st_size
                )
                
                backups.append(backup_info)
                
            except Exception as e:
                logger.warning(f"Failed to read backup metadata from {backup_file}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda b: b.timestamp, reverse=True)
        
        return backups
    
    def restore_backup(self, backup_path: Path) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Restore configuration from backup
        
        Returns:
            Tuple of (success, config_data, errors)
        """
        errors = []
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Remove backup metadata
            if "_backup_metadata" in backup_data:
                del backup_data["_backup_metadata"]
            
            # Validate restored configuration
            is_valid, validation_errors, warnings = self.validate_configuration(backup_data)
            if not is_valid:
                errors.extend(validation_errors)
                return False, backup_data, errors
            
            if warnings:
                logger.warning(f"Backup restore warnings: {'; '.join(warnings)}")
            
            logger.info(f"Configuration restored from backup: {backup_path}")
            return True, backup_data, errors
            
        except Exception as e:
            errors.append(f"Failed to restore backup: {e}")
            logger.error(f"Failed to restore backup from {backup_path}: {e}")
            return False, None, errors
    
    def cleanup_backups(self, backup_dir: Path, keep_count: int = 10) -> int:
        """
        Clean up old backups, keeping only the specified number
        
        Returns:
            Number of backups removed
        """
        backups = self.list_backups(backup_dir)
        
        if len(backups) <= keep_count:
            return 0
        
        # Remove oldest backups
        backups_to_remove = backups[keep_count:]
        removed_count = 0
        
        for backup in backups_to_remove:
            try:
                backup.path.unlink()
                removed_count += 1
                logger.debug(f"Removed old backup: {backup.path}")
            except Exception as e:
                logger.warning(f"Failed to remove backup {backup.path}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old configuration backups")
        
        return removed_count
    
    def compare_configurations(self, 
                             config1: Dict[str, Any], 
                             config2: Dict[str, Any]) -> ConfigurationDiff:
        """Compare two configurations and return differences"""
        
        flat1 = self._flatten_dict(config1)
        flat2 = self._flatten_dict(config2)
        
        all_keys = set(flat1.keys()) | set(flat2.keys())
        
        added = {}
        removed = {}
        modified = {}
        unchanged = {}
        
        for key in all_keys:
            if key in flat1 and key in flat2:
                if flat1[key] == flat2[key]:
                    unchanged[key] = flat1[key]
                else:
                    modified[key] = (flat1[key], flat2[key])
            elif key in flat1:
                removed[key] = flat1[key]
            else:
                added[key] = flat2[key]
        
        return ConfigurationDiff(
            added=added,
            removed=removed,
            modified=modified,
            unchanged=unchanged
        )
    
    def generate_configuration_report(self, config: Dict[str, Any]) -> str:
        """Generate a human-readable configuration report"""
        report_lines = []
        report_lines.append("VidTanium Configuration Report")
        report_lines.append("=" * 40)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Schema Version: {self.schema.schema_version}")
        report_lines.append("")
        
        # Validation status
        is_valid, errors, warnings = self.validate_configuration(config)
        report_lines.append(f"Validation Status: {'✓ Valid' if is_valid else '✗ Invalid'}")
        
        if errors:
            report_lines.append("Errors:")
            for error in errors:
                report_lines.append(f"  - {error}")
        
        if warnings:
            report_lines.append("Warnings:")
            for warning in warnings:
                report_lines.append(f"  - {warning}")
        
        report_lines.append("")
        
        # Configuration sections
        for section_name, section_config in config.items():
            if section_name.startswith("_"):
                continue
                
            report_lines.append(f"[{section_name.upper()}]")
            
            if isinstance(section_config, dict):
                for key, value in section_config.items():
                    report_lines.append(f"  {key}: {value}")
            else:
                report_lines.append(f"  {section_config}")
            
            report_lines.append("")
        
        # Feature flags (if available)
        if self.feature_manager:
            enabled_features = self.feature_manager.get_enabled_features()
            if enabled_features:
                report_lines.append("[ENABLED FEATURES]")
                for feature in sorted(enabled_features):
                    feature_info = self.feature_manager.get_feature_info(feature)
                    if feature_info:
                        report_lines.append(f"  {feature}: {feature_info.description}")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary for comparison"""
        items: List[Tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
