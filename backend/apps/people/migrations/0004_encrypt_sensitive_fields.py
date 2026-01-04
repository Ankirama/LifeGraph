"""
Migration to encrypt sensitive personal data fields.

This migration converts plain text fields to encrypted fields using
Fernet encryption (AES-128-CBC with HMAC).

IMPORTANT:
- Set FERNET_KEYS environment variable before running this migration
- Back up your database before running this migration
- Data encrypted with this key cannot be recovered without the key
"""

from django.db import migrations

import apps.core.encryption


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0003_add_is_owner_field"),
    ]

    operations = [
        # Person model - sensitive contact and personal info
        migrations.AlterField(
            model_name="person",
            name="met_context",
            field=apps.core.encryption.EncryptedTextField(
                blank=True,
                help_text="How/where you met this person (encrypted)",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="emails",
            field=apps.core.encryption.EncryptedJSONField(
                blank=True,
                default=list,
                help_text='List of {"email": "...", "label": "work/personal/..."} (encrypted)',
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="phones",
            field=apps.core.encryption.EncryptedJSONField(
                blank=True,
                default=list,
                help_text='List of {"phone": "...", "label": "mobile/home/..."} (encrypted)',
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="addresses",
            field=apps.core.encryption.EncryptedJSONField(
                blank=True,
                default=list,
                help_text='List of {"address": "...", "label": "home/work/..."} (encrypted)',
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="notes",
            field=apps.core.encryption.EncryptedTextField(
                blank=True,
                help_text="General notes about this person (encrypted)",
            ),
        ),
        # Relationship model - notes about relationships
        migrations.AlterField(
            model_name="relationship",
            name="notes",
            field=apps.core.encryption.EncryptedTextField(
                blank=True,
                help_text="Notes about this relationship (encrypted)",
            ),
        ),
        # Anecdote model - personal memories and stories
        migrations.AlterField(
            model_name="anecdote",
            name="content",
            field=apps.core.encryption.EncryptedTextField(
                help_text="Rich text / Markdown content (encrypted)",
            ),
        ),
        # CustomFieldValue - user-defined sensitive data
        migrations.AlterField(
            model_name="customfieldvalue",
            name="value",
            field=apps.core.encryption.EncryptedJSONField(
                help_text="Flexible storage for any field type (encrypted)",
            ),
        ),
        # Employment model - job descriptions
        migrations.AlterField(
            model_name="employment",
            name="description",
            field=apps.core.encryption.EncryptedTextField(
                blank=True,
                help_text="Job description (encrypted)",
            ),
        ),
    ]
