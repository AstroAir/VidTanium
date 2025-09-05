"""
Configuration Migration System

Handles configuration versioning and automatic migration between versions
to maintain backward compatibility.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class MigrationRule:
    """Configuration migration rule"""
    from_version: str
    to_version: str
    description: str
    migration_function: Callable[[Dict[str, Any]], Dict[str, Any]]
    required: bool = True
    backup_before: bool = True


@dataclass
class MigrationResult:
    """Result of configuration migration"""
    success: bool
    from_version: str
    to_version: str
    errors: List[str]
    warnings: List[str]
    migrated_config: Optional[Dict[str, Any]] = None
    backup_path: Optional[Path] = None
    changes_made: Optional[List[str]] = None


class ConfigurationMigrator:
    """Handles configuration version migration"""
    
    def __init__(self, target_version: str = "2.0.0"):
        self.target_version = target_version
        self.migration_rules: List[MigrationRule] = []
        self._register_default_migrations()
    
    def _register_default_migrations(self) -> None:
        """Register default migration rules"""
        
        # Migration from 1.0.0 to 2.0.0
        self.migration_rules.append(MigrationRule(
            from_version="1.0.0",
            to_version="2.0.0",
            description="Migrate from legacy configuration format to enhanced schema",
            migration_function=self._migrate_1_0_to_2_0,
            required=True,
            backup_before=True
        ))
        
        # Migration for configurations without version (assume 1.0.0)
        self.migration_rules.append(MigrationRule(
            from_version="",
            to_version="2.0.0",
            description="Migrate legacy configuration without version to enhanced schema",
            migration_function=self._migrate_legacy_to_2_0,
            required=True,
            backup_before=True
        ))
    
    def get_config_version(self, config: Dict[str, Any]) -> str:
        """Get configuration version"""
        version = config.get("_version", config.get("version", ""))
        return str(version) if version is not None else ""
    
    def needs_migration(self, config: Dict[str, Any]) -> bool:
        """Check if configuration needs migration"""
        current_version = self.get_config_version(config)
        return current_version != self.target_version
    
    def migrate_configuration(self, 
                            config: Dict[str, Any], 
                            config_file_path: Optional[Path] = None) -> MigrationResult:
        """
        Migrate configuration to target version
        
        Args:
            config: Configuration dictionary to migrate
            config_file_path: Path to configuration file for backup
            
        Returns:
            MigrationResult with migration details
        """
        current_version = self.get_config_version(config)
        errors: List[str] = []
        warnings: List[str] = []
        changes_made: List[str] = []
        backup_path: Optional[Path] = None
        
        logger.info(f"Starting migration from version {current_version} to {self.target_version}")
        
        # Create backup if requested and file path provided
        if config_file_path and config_file_path.exists():
            try:
                backup_path = self._create_backup(config_file_path)
                logger.info(f"Created configuration backup at {backup_path}")
            except Exception as e:
                errors.append(f"Failed to create backup: {e}")
                logger.error(f"Failed to create backup: {e}")
        
        # Find applicable migration rules
        applicable_rules = self._find_migration_path(current_version, self.target_version)
        
        if not applicable_rules:
            if current_version == self.target_version:
                return MigrationResult(
                    success=True,
                    from_version=current_version,
                    to_version=self.target_version,
                    errors=[],
                    warnings=["Configuration is already at target version"],
                    backup_path=backup_path,
                    changes_made=[]
                )
            else:
                return MigrationResult(
                    success=False,
                    from_version=current_version,
                    to_version=self.target_version,
                    errors=[f"No migration path found from {current_version} to {self.target_version}"],
                    warnings=warnings,
                    backup_path=backup_path,
                    changes_made=changes_made
                )
        
        # Apply migration rules in sequence
        migrated_config = config.copy()
        
        for rule in applicable_rules:
            try:
                logger.info(f"Applying migration rule: {rule.description}")
                old_config = migrated_config.copy()
                migrated_config = rule.migration_function(migrated_config)
                
                # Track changes
                changes = self._detect_changes(old_config, migrated_config)
                changes_made.extend(changes)
                
                logger.info(f"Successfully applied migration from {rule.from_version} to {rule.to_version}")
                
            except Exception as e:
                error_msg = f"Migration rule failed ({rule.from_version} -> {rule.to_version}): {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                
                if rule.required:
                    return MigrationResult(
                        success=False,
                        from_version=current_version,
                        to_version=self.target_version,
                        errors=errors,
                        warnings=warnings,
                        backup_path=backup_path,
                        changes_made=changes_made
                    )
        
        # Set target version
        migrated_config["_version"] = self.target_version
        changes_made.append(f"Set configuration version to {self.target_version}")
        
        success = len(errors) == 0
        
        return MigrationResult(
            success=success,
            from_version=current_version,
            to_version=self.target_version,
            errors=errors,
            warnings=warnings,
            migrated_config=migrated_config if success else None,
            backup_path=backup_path,
            changes_made=changes_made
        )
    
    def _find_migration_path(self, from_version: str, to_version: str) -> List[MigrationRule]:
        """Find migration path from source to target version"""
        # For now, use direct migration rules
        # In the future, this could implement graph-based path finding for complex migrations
        
        applicable_rules = []
        
        for rule in self.migration_rules:
            if rule.from_version == from_version and rule.to_version == to_version:
                applicable_rules.append(rule)
                break
        
        return applicable_rules
    
    def _create_backup(self, config_file_path: Path) -> Path:
        """Create backup of configuration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{config_file_path.stem}_backup_{timestamp}{config_file_path.suffix}"
        backup_path = config_file_path.parent / "backups" / backup_filename
        
        # Ensure backup directory exists
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(config_file_path, backup_path)
        
        return backup_path
    
    def _detect_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[str]:
        """Detect changes between configurations"""
        changes = []
        
        # Simple change detection - could be enhanced for more detailed reporting
        old_keys = set(self._flatten_dict(old_config).keys())
        new_keys = set(self._flatten_dict(new_config).keys())
        
        added_keys = new_keys - old_keys
        removed_keys = old_keys - new_keys
        
        for key in added_keys:
            changes.append(f"Added configuration key: {key}")
        
        for key in removed_keys:
            changes.append(f"Removed configuration key: {key}")
        
        return changes
    
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
    
    def _migrate_1_0_to_2_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 1.0.0 to 2.0.0"""
        migrated = config.copy()
        
        # Add new sections with defaults
        if "network" not in migrated:
            migrated["network"] = {
                "connection_pool_size": 20,
                "max_connections_per_host": 8,
                "connection_timeout": 30.0,
                "read_timeout": 120.0,
                "dns_cache_timeout": 300,
                "keep_alive_timeout": 300.0,
                "proxy": migrated.get("advanced", {}).get("proxy", ""),
                "user_agent": migrated.get("advanced", {}).get("user_agent", 
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
                "verify_ssl": migrated.get("advanced", {}).get("verify_ssl", True)
            }
        
        if "performance" not in migrated:
            migrated["performance"] = {
                "memory_limit_mb": 1024,
                "cpu_usage_limit": 80,
                "buffer_size_min": 8192,
                "buffer_size_max": 1048576,
                "buffer_size_default": 65536,
                "gc_threshold_mb": 100,
                "optimization_level": "balanced"
            }
        
        if "logging" not in migrated:
            migrated["logging"] = {
                "log_level": "INFO",
                "debug_logging": migrated.get("advanced", {}).get("debug_logging", False),
                "log_to_file": True,
                "log_to_console": True,
                "log_file_path": "",
                "log_rotation_size": "10 MB",
                "log_retention": "7 days",
                "log_compression": "zip"
            }
        
        # Migrate existing settings
        if "general" in migrated:
            general = migrated["general"]
            
            # Add new general settings with defaults
            general.setdefault("temp_directory", "")
            general.setdefault("cache_directory", "")
            general.setdefault("backup_directory", "")
            general.setdefault("config_auto_save", True)
            general.setdefault("config_backup_count", 5)
        
        # Remove deprecated advanced section settings that moved to network
        if "advanced" in migrated:
            advanced = migrated["advanced"]
            # Keep ffmpeg_path and keep_temp_files, remove others that moved
            new_advanced = {
                "ffmpeg_path": advanced.get("ffmpeg_path", ""),
                "keep_temp_files": advanced.get("keep_temp_files", False)
            }
            migrated["advanced"] = new_advanced
        
        return migrated
    
    def _migrate_legacy_to_2_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy configuration (no version) to 2.0.0"""
        # Treat as 1.0.0 and migrate
        return self._migrate_1_0_to_2_0(config)
