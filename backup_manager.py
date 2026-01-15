"""
Automated backup and data management system.
Ensures your work is never lost.
"""
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import zipfile

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Automated backup system for all user data.
    
    Features:
    - Automatic daily backups
    - Manual backup on demand
    - Export to multiple formats
    - Restore from backup
    - Backup rotation (keep last N backups)
    """
    
    def __init__(self, backup_dir: str = "backups", max_backups: int = 30):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to keep
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = max_backups
        
        logger.info(f"Backup manager initialized: {backup_dir}, keeping {max_backups} backups")
    
    def create_backup(self, include_db: bool = True, include_cache: bool = False) -> str:
        """
        Create a full backup of all data.
        
        Args:
            include_db: Include database
            include_cache: Include cache files
            
        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"Creating backup: {backup_name}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup database
                if include_db:
                    db_path = Path("prompt_optimizer.db")
                    if db_path.exists():
                        zipf.write(db_path, "database/prompt_optimizer.db")
                        logger.debug("Added database to backup")
                
                # Backup cache
                if include_cache:
                    cache_dir = Path(".cache")
                    if cache_dir.exists():
                        for cache_file in cache_dir.glob("*.pkl"):
                            zipf.write(cache_file, f"cache/{cache_file.name}")
                        logger.debug("Added cache to backup")
                
                # Backup knowledge bases
                kb_dir = Path("knowledge_bases")
                if kb_dir.exists():
                    for kb_folder in kb_dir.iterdir():
                        if kb_folder.is_dir():
                            for file in kb_folder.rglob("*"):
                                if file.is_file():
                                    zipf.write(file, f"knowledge_bases/{file.relative_to(kb_dir)}")
                    logger.debug("Added knowledge bases to backup")
                
                # Add metadata
                metadata = {
                    "timestamp": timestamp,
                    "version": "1.0.0",
                    "includes": {
                        "database": include_db,
                        "cache": include_cache
                    }
                }
                zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            logger.info(f"Backup created successfully: {backup_path}")
            
            # Rotate old backups
            self._rotate_backups()
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore from a backup file.
        
        Args:
            backup_path: Path to backup zip file
            
        Returns:
            True if successful
        """
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        logger.info(f"Restoring from backup: {backup_path}")
        
        try:
            # Create restore directory
            restore_dir = Path("restore_temp")
            restore_dir.mkdir(exist_ok=True)
            
            # Extract backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            # Restore database
            db_backup = restore_dir / "database" / "prompt_optimizer.db"
            if db_backup.exists():
                shutil.copy(db_backup, "prompt_optimizer.db")
                logger.info("Database restored")
            
            # Restore cache
            cache_backup_dir = restore_dir / "cache"
            if cache_backup_dir.exists():
                cache_dir = Path(".cache")
                cache_dir.mkdir(exist_ok=True)
                for cache_file in cache_backup_dir.glob("*.pkl"):
                    shutil.copy(cache_file, cache_dir / cache_file.name)
                logger.info("Cache restored")
            
            # Restore knowledge bases
            kb_backup_dir = restore_dir / "knowledge_bases"
            if kb_backup_dir.exists():
                kb_dir = Path("knowledge_bases")
                if kb_dir.exists():
                    shutil.rmtree(kb_dir)
                shutil.copytree(kb_backup_dir, kb_dir)
                logger.info("Knowledge bases restored")
            
            # Cleanup
            shutil.rmtree(restore_dir)
            
            logger.info("Restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """
        List all available backups.
        
        Returns:
            List of backup info dictionaries
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("backup_*.zip"), reverse=True):
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if "metadata.json" in zipf.namelist():
                        metadata = json.loads(zipf.read("metadata.json"))
                    else:
                        metadata = {}
                
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size_mb": backup_file.stat().st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(backup_file.stat().st_mtime),
                    "metadata": metadata
                })
            except Exception as e:
                logger.warning(f"Could not read backup {backup_file}: {str(e)}")
        
        return backups
    
    def _rotate_backups(self):
        """Remove old backups beyond max_backups limit."""
        backups = sorted(self.backup_dir.glob("backup_*.zip"))
        
        if len(backups) > self.max_backups:
            for old_backup in backups[:-self.max_backups]:
                old_backup.unlink()
                logger.info(f"Rotated old backup: {old_backup.name}")
    
    def export_to_json(self, output_path: str) -> bool:
        """
        Export all data to a single JSON file.
        
        Args:
            output_path: Path to output JSON file
            
        Returns:
            True if successful
        """
        try:
            from database import db
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "version": "1.0.0",
                "data": {
                    "sessions": [],
                    "saved_prompts": [],
                    "blueprints": []
                }
            }
            
            # Export sessions (last 100)
            sessions = db.get_user_sessions(user_id=1, limit=100)
            for session in sessions:
                export_data["data"]["sessions"].append({
                    "id": session.id,
                    "original_prompt": session.original_prompt,
                    "optimized_prompt": session.optimized_prompt,
                    "quality_score": session.quality_score,
                    "created_at": session.created_at.isoformat()
                })
            
            # Export saved prompts
            saved_prompts = db.get_saved_prompts()
            for prompt in saved_prompts:
                export_data["data"]["saved_prompts"].append({
                    "id": prompt.id,
                    "name": prompt.name,
                    "optimized_prompt": prompt.optimized_prompt,
                    "prompt_type": prompt.prompt_type,
                    "quality_score": prompt.quality_score,
                    "tags": json.loads(prompt.tags) if prompt.tags else []
                })
            
            # Export blueprints
            blueprints = db.get_blueprints()
            export_data["data"]["blueprints"] = blueprints
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported data to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return False


# Global backup manager
_backup_manager = BackupManager()


def get_backup_manager() -> BackupManager:
    """Get global backup manager."""
    return _backup_manager


def auto_backup():
    """Create automatic backup (call this periodically)."""
    try:
        _backup_manager.create_backup(include_db=True, include_cache=False)
        logger.info("Automatic backup completed")
    except Exception as e:
        logger.error(f"Automatic backup failed: {str(e)}")
