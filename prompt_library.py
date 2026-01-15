"""
Prompt Library Management Module
Handles saving, organizing, and retrieving optimized prompts.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from database import db, SavedPrompt

logger = logging.getLogger(__name__)


class PromptLibrary:
    """Manages the user's prompt library."""

    @staticmethod
    def save_prompt(
        name: str,
        optimized_prompt: str,
        original_prompt: Optional[str] = None,
        prompt_type: Optional[str] = None,
        quality_score: Optional[int] = None,
        tags: Optional[List[str]] = None,
        folder: str = "default",
        is_template: bool = False,
        notes: Optional[str] = None
    ) -> Optional[SavedPrompt]:
        """
        Save an optimized prompt to the library.

        Args:
            name: Display name for the prompt
            optimized_prompt: The optimized prompt text
            original_prompt: Original prompt (optional)
            prompt_type: Type of prompt
            quality_score: Quality score 0-100
            tags: List of tags for categorization
            folder: Folder name for organization
            is_template: Whether this is a reusable template
            notes: Additional notes

        Returns:
            SavedPrompt object or None on failure
        """
        return db.save_prompt(
            name=name,
            optimized_prompt=optimized_prompt,
            original_prompt=original_prompt,
            prompt_type=prompt_type,
            quality_score=quality_score,
            tags=tags,
            folder=folder,
            is_template=is_template,
            notes=notes
        )

    @staticmethod
    def get_prompts(
        folder: Optional[str] = None,
        prompt_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: Optional[bool] = None,
        search_query: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get saved prompts with optional filtering.

        Args:
            folder: Filter by folder name
            prompt_type: Filter by prompt type
            tags: Filter by tags (prompt must have any of these tags)
            is_template: Filter by template status
            search_query: Search in name, notes, and prompt content
            limit: Maximum number of results

        Returns:
            List of prompt dictionaries
        """
        prompts = db.get_saved_prompts(
            folder=folder,
            prompt_type=prompt_type,
            tags=tags,
            is_template=is_template,
            search_query=search_query
        )

        # Convert to dictionaries and limit if specified
        result = []
        for prompt in prompts[:limit] if limit else prompts:
            prompt_dict = {
                "id": prompt.id,
                "name": prompt.name,
                "original_prompt": prompt.original_prompt,
                "optimized_prompt": prompt.optimized_prompt,
                "prompt_type": prompt.prompt_type,
                "quality_score": prompt.quality_score,
                "folder": prompt.folder,
                "is_template": prompt.is_template,
                "notes": prompt.notes,
                "created_at": prompt.created_at.isoformat(),
                "updated_at": prompt.updated_at.isoformat(),
                "tags": []
            }

            # Parse tags from JSON
            if prompt.tags:
                try:
                    prompt_dict["tags"] = json.loads(prompt.tags)
                except json.JSONDecodeError:
                    prompt_dict["tags"] = []

            result.append(prompt_dict)

        return result

    @staticmethod
    def get_prompt(prompt_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific prompt by ID."""
        prompt = db.get_saved_prompt(prompt_id)
        if not prompt:
            return None

        prompt_dict = {
            "id": prompt.id,
            "name": prompt.name,
            "original_prompt": prompt.original_prompt,
            "optimized_prompt": prompt.optimized_prompt,
            "prompt_type": prompt.prompt_type,
            "quality_score": prompt.quality_score,
            "folder": prompt.folder,
            "is_template": prompt.is_template,
            "notes": prompt.notes,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat(),
            "tags": []
        }

        # Parse tags from JSON
        if prompt.tags:
            try:
                prompt_dict["tags"] = json.loads(prompt.tags)
            except json.JSONDecodeError:
                prompt_dict["tags"] = []

        return prompt_dict

    @staticmethod
    def update_prompt(
        prompt_id: int,
        name: Optional[str] = None,
        optimized_prompt: Optional[str] = None,
        original_prompt: Optional[str] = None,
        prompt_type: Optional[str] = None,
        quality_score: Optional[int] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        is_template: Optional[bool] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update a saved prompt."""
        updates = {}
        if name is not None:
            updates["name"] = name
        if optimized_prompt is not None:
            updates["optimized_prompt"] = optimized_prompt
        if original_prompt is not None:
            updates["original_prompt"] = original_prompt
        if prompt_type is not None:
            updates["prompt_type"] = prompt_type
        if quality_score is not None:
            updates["quality_score"] = quality_score
        if tags is not None:
            updates["tags"] = tags
        if folder is not None:
            updates["folder"] = folder
        if is_template is not None:
            updates["is_template"] = is_template
        if notes is not None:
            updates["notes"] = notes

        if not updates:
            return True  # No changes needed

        return db.update_saved_prompt(prompt_id, **updates) is not None

    @staticmethod
    def delete_prompt(prompt_id: int) -> bool:
        """Delete a saved prompt."""
        return db.delete_saved_prompt(prompt_id)

    @staticmethod
    def get_folders() -> List[str]:
        """Get all folder names."""
        return db.get_folders()

    @staticmethod
    def get_tags() -> List[str]:
        """Get all unique tags."""
        return db.get_tags()

    @staticmethod
    def export_library(
        folder: Optional[str] = None,
        prompt_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Export the prompt library to a structured format.

        Args:
            folder: Filter by folder
            prompt_type: Filter by prompt type
            tags: Filter by tags
            is_template: Filter by template status

        Returns:
            Dictionary with export data
        """
        import datetime

        prompts = PromptLibrary.get_prompts(
            folder=folder,
            prompt_type=prompt_type,
            tags=tags,
            is_template=is_template
        )

        export_data = {
            "exported_at": datetime.datetime.now().isoformat(),
            "version": "2.0",
            "total_prompts": len(prompts),
            "filters_applied": {
                "folder": folder,
                "prompt_type": prompt_type,
                "tags": tags,
                "is_template": is_template
            },
            "prompts": prompts
        }

        return export_data

    @staticmethod
    def import_library(export_data: Dict[str, Any], folder_prefix: str = "") -> Dict[str, int]:
        """
        Import prompts from an export file.

        Args:
            export_data: Export data dictionary
            folder_prefix: Prefix to add to folder names

        Returns:
            Dictionary with import statistics
        """
        if "prompts" not in export_data:
            raise ValueError("Invalid export data format")

        imported = 0
        skipped = 0
        errors = 0

        for prompt_data in export_data["prompts"]:
            try:
                # Skip if prompt with same name already exists
                existing = db.get_saved_prompts(search_query=prompt_data.get("name"))
                if existing:
                    skipped += 1
                    continue

                # Create new prompt
                folder = folder_prefix + prompt_data.get("folder", "imported")
                if folder_prefix and not folder.startswith(folder_prefix):
                    folder = folder_prefix + folder

                success = PromptLibrary.save_prompt(
                    name=prompt_data["name"],
                    optimized_prompt=prompt_data["optimized_prompt"],
                    original_prompt=prompt_data.get("original_prompt"),
                    prompt_type=prompt_data.get("prompt_type"),
                    quality_score=prompt_data.get("quality_score"),
                    tags=prompt_data.get("tags", []),
                    folder=folder,
                    is_template=prompt_data.get("is_template", False),
                    notes=prompt_data.get("notes")
                )

                if success:
                    imported += 1
                else:
                    errors += 1

            except Exception as e:
                logger.error(f"Error importing prompt '{prompt_data.get('name', 'unknown')}': {str(e)}")
                errors += 1

        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors
        }

    @staticmethod
    def create_template(
        name: str,
        template_prompt: str,
        prompt_type: str,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> Optional[SavedPrompt]:
        """
        Create a reusable prompt template.

        Args:
            name: Template name
            template_prompt: The template prompt text
            prompt_type: Type of prompt this template is for
            description: Description of the template
            tags: Tags for the template

        Returns:
            SavedPrompt object or None on failure
        """
        return PromptLibrary.save_prompt(
            name=name,
            optimized_prompt=template_prompt,
            prompt_type=prompt_type,
            folder="templates",
            is_template=True,
            notes=description,
            tags=tags or ["template"]
        )

    @staticmethod
    def get_templates(prompt_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all available templates."""
        return PromptLibrary.get_prompts(
            is_template=True,
            folder="templates",
            prompt_type=prompt_type
        )


# Initialize default templates
def initialize_default_templates():
    """Create default templates if they don't exist."""
    # Check if templates already exist
    existing_templates = PromptLibrary.get_templates()
    if existing_templates:
        return  # Already initialized

    # Import templates from templates.py
    from templates import ALL_TEMPLATES

    for template in ALL_TEMPLATES:
        PromptLibrary.create_template(
            name=template.name,
            template_prompt=template.template,
            prompt_type=template.prompt_type,
            description=template.description,
            tags=template.tags
        )

    logger.info(f"Initialized {len(ALL_TEMPLATES)} default templates")


# Initialize templates on module import
try:
    initialize_default_templates()
except Exception as e:
    logger.warning(f"Could not initialize default templates: {str(e)}")