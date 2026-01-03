"""
Core models - base classes and shared models.
"""

import uuid

from django.db import models


class BaseModel(models.Model):
    """Abstract base model with common fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tag(BaseModel):
    """Tags for categorizing persons and anecdotes."""

    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default="#6366f1")  # Hex color
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Group(BaseModel):
    """Hierarchical groups for organizing persons."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    color = models.CharField(max_length=7, default="#8b5cf6")  # Hex color

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "parent"],
                name="unique_group_name_per_parent",
            )
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    @property
    def full_path(self) -> str:
        """Return the full hierarchical path."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
