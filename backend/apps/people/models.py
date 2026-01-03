"""
People app models - Person, Relationship, RelationshipType, Anecdote.
"""

from django.db import models

from apps.core.models import BaseModel, Group, Tag


class Person(BaseModel):
    """
    Core person model representing a contact in the CRM.
    """

    # Identity
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)

    # Dates
    birthday = models.DateField(null=True, blank=True)
    met_date = models.DateField(null=True, blank=True)
    met_context = models.TextField(blank=True, help_text="How/where you met this person")

    # Contact Information (JSON for flexibility)
    emails = models.JSONField(
        default=list,
        blank=True,
        help_text='List of {"email": "...", "label": "work/personal/..."}',
    )
    phones = models.JSONField(
        default=list,
        blank=True,
        help_text='List of {"phone": "...", "label": "mobile/home/..."}',
    )
    addresses = models.JSONField(
        default=list,
        blank=True,
        help_text='List of {"address": "...", "label": "home/work/..."}',
    )

    # Social
    linkedin_url = models.URLField(blank=True)
    discord_id = models.CharField(max_length=50, blank=True)

    # Metadata
    notes = models.TextField(blank=True, help_text="General notes about this person")
    is_active = models.BooleanField(default=True, help_text="Soft delete flag")
    is_owner = models.BooleanField(default=False, help_text="True if this is the CRM owner (you)")

    # AI
    ai_summary = models.TextField(blank=True, help_text="AI-generated summary")
    ai_summary_updated = models.DateTimeField(null=True, blank=True)

    # Tracking
    last_contact = models.DateTimeField(null=True, blank=True)

    # Relations
    groups = models.ManyToManyField(Group, related_name="persons", blank=True)
    tags = models.ManyToManyField(Tag, related_name="persons", blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name_plural = "People"

    def __str__(self):
        full_name = self.full_name
        if self.nickname:
            return f"{full_name} ({self.nickname})"
        return full_name

    @property
    def full_name(self) -> str:
        """Return the full name (first + last)."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def primary_email(self) -> str | None:
        """Return the first email address."""
        if self.emails and len(self.emails) > 0:
            return self.emails[0].get("email")
        return None

    @property
    def primary_phone(self) -> str | None:
        """Return the first phone number."""
        if self.phones and len(self.phones) > 0:
            return self.phones[0].get("phone")
        return None


class RelationshipType(BaseModel):
    """
    Types of relationships (spouse, friend, colleague, etc).
    """

    class Category(models.TextChoices):
        FAMILY = "family", "Family"
        PROFESSIONAL = "professional", "Professional"
        SOCIAL = "social", "Social"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=100, unique=True)
    inverse_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name when viewed from the other person's perspective",
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.SOCIAL,
    )
    is_symmetric = models.BooleanField(
        default=False,
        help_text="True if relationship is the same both ways (e.g., spouse, friend)",
    )
    auto_create_inverse = models.BooleanField(
        default=True,
        help_text="Automatically create inverse relationship",
    )

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If symmetric and no inverse name, use the same name
        if self.is_symmetric and not self.inverse_name:
            self.inverse_name = self.name
        super().save(*args, **kwargs)


class Relationship(BaseModel):
    """
    Relationship between two persons.
    """

    person_a = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="relationships_as_a",
    )
    person_b = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="relationships_as_b",
    )
    relationship_type = models.ForeignKey(
        RelationshipType,
        on_delete=models.PROTECT,
        related_name="relationships",
    )

    # Metadata
    started_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    strength = models.IntegerField(
        null=True,
        blank=True,
        help_text="Relationship strength 1-5",
    )

    # System
    auto_created = models.BooleanField(
        default=False,
        help_text="True if this was auto-created as inverse",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["person_a", "person_b", "relationship_type"],
                name="unique_relationship",
            ),
            models.CheckConstraint(
                check=~models.Q(person_a=models.F("person_b")),
                name="no_self_relationship",
            ),
        ]

    def __str__(self):
        return f"{self.person_a.full_name} → {self.relationship_type.name} → {self.person_b.full_name}"


class Anecdote(BaseModel):
    """
    Memories, jokes, quotes, and notes about persons.
    """

    class AnecdoteType(models.TextChoices):
        MEMORY = "memory", "Memory"
        JOKE = "joke", "Joke"
        QUOTE = "quote", "Quote"
        NOTE = "note", "Note"

    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(help_text="Rich text / Markdown content")
    date = models.DateField(null=True, blank=True, help_text="When this happened")
    location = models.CharField(max_length=255, blank=True)

    # Relations
    persons = models.ManyToManyField(Person, related_name="anecdotes")

    # Categorization
    anecdote_type = models.CharField(
        max_length=20,
        choices=AnecdoteType.choices,
        default=AnecdoteType.NOTE,
    )
    tags = models.ManyToManyField(Tag, related_name="anecdotes", blank=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        if self.title:
            return self.title
        return f"{self.anecdote_type} - {self.created_at.strftime('%Y-%m-%d')}"


class CustomFieldDefinition(BaseModel):
    """
    Definition for custom fields on Person.
    """

    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        DATE = "date", "Date"
        SELECT = "select", "Select"
        MULTISELECT = "multiselect", "Multi-Select"

    name = models.CharField(max_length=100, unique=True)
    field_type = models.CharField(max_length=20, choices=FieldType.choices)
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="Options for select/multiselect types",
    )
    is_required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} ({self.field_type})"


class CustomFieldValue(BaseModel):
    """
    Value of a custom field for a specific person.
    """

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="custom_field_values",
    )
    definition = models.ForeignKey(
        CustomFieldDefinition,
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.JSONField(help_text="Flexible storage for any field type")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "definition"],
                name="unique_custom_field_per_person",
            )
        ]

    def __str__(self):
        return f"{self.person.full_name} - {self.definition.name}"


class Photo(BaseModel):
    """
    Photos associated with persons.
    """

    file = models.FileField(upload_to="photos/%Y/%m/")
    caption = models.CharField(max_length=500, blank=True)

    # Metadata
    date_taken = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    location_coords = models.JSONField(
        null=True,
        blank=True,
        help_text='{"lat": float, "lng": float}',
    )

    # AI
    ai_description = models.TextField(blank=True, help_text="AI-generated description")
    detected_faces = models.JSONField(
        default=list,
        blank=True,
        help_text="List of detected face regions for tagging assistance",
    )

    # Relations
    persons = models.ManyToManyField(Person, related_name="photos", blank=True)
    anecdote = models.ForeignKey(
        Anecdote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="photos",
    )

    class Meta:
        ordering = ["-date_taken", "-created_at"]

    def __str__(self):
        if self.caption:
            return self.caption[:50]
        return f"Photo {self.id}"


class Employment(BaseModel):
    """
    Employment/professional history for a person.
    """

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="employments",
    )

    # Job details
    company = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=255, blank=True)

    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    # Additional info
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # LinkedIn sync
    linkedin_synced = models.BooleanField(default=False)
    linkedin_last_sync = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-is_current", "-start_date"]
        verbose_name_plural = "Employment history"

    def __str__(self):
        current = " (current)" if self.is_current else ""
        return f"{self.person.full_name} - {self.title} at {self.company}{current}"

    def save(self, *args, **kwargs):
        # If this is marked as current, unmark other current jobs
        if self.is_current:
            Employment.objects.filter(
                person=self.person,
                is_current=True,
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)
