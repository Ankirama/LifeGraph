"""
Tests for CustomFieldDefinition and CustomFieldValue models.
"""

import pytest
from django.db import IntegrityError

from apps.people.models import CustomFieldDefinition, CustomFieldValue
from tests.factories import (
    CustomFieldDefinitionFactory,
    CustomFieldValueFactory,
    DateCustomFieldDefinitionFactory,
    MultiSelectCustomFieldDefinitionFactory,
    NumberCustomFieldDefinitionFactory,
    PersonFactory,
    SelectCustomFieldDefinitionFactory,
)


# =============================================================================
# CustomFieldDefinition Creation Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldDefinitionCreation:
    """Tests for CustomFieldDefinition model creation."""

    def test_create_text_field(self):
        """Test creating a text custom field definition."""
        cfd = CustomFieldDefinitionFactory(
            name="Hobbies",
            field_type=CustomFieldDefinition.FieldType.TEXT,
        )

        assert cfd.name == "Hobbies"
        assert cfd.field_type == CustomFieldDefinition.FieldType.TEXT
        assert cfd.pk is not None

    def test_create_number_field(self):
        """Test creating a number custom field definition."""
        cfd = NumberCustomFieldDefinitionFactory(name="Age")

        assert cfd.field_type == CustomFieldDefinition.FieldType.NUMBER

    def test_create_date_field(self):
        """Test creating a date custom field definition."""
        cfd = DateCustomFieldDefinitionFactory(name="Anniversary")

        assert cfd.field_type == CustomFieldDefinition.FieldType.DATE

    def test_create_select_field(self):
        """Test creating a select custom field definition."""
        cfd = SelectCustomFieldDefinitionFactory(name="Priority")

        assert cfd.field_type == CustomFieldDefinition.FieldType.SELECT
        assert len(cfd.options) == 3

    def test_create_multiselect_field(self):
        """Test creating a multi-select custom field definition."""
        cfd = MultiSelectCustomFieldDefinitionFactory(name="Skills")

        assert cfd.field_type == CustomFieldDefinition.FieldType.MULTISELECT
        assert len(cfd.options) == 4

    def test_unique_name(self):
        """Test that custom field names must be unique."""
        CustomFieldDefinitionFactory(name="Unique Field")

        with pytest.raises(IntegrityError):
            CustomFieldDefinition.objects.create(
                name="Unique Field",
                field_type=CustomFieldDefinition.FieldType.TEXT,
            )


# =============================================================================
# CustomFieldDefinition Options Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldDefinitionOptions:
    """Tests for CustomFieldDefinition options field."""

    def test_options_default_empty(self):
        """Test that options default to empty list."""
        cfd = CustomFieldDefinitionFactory(
            field_type=CustomFieldDefinition.FieldType.TEXT,
        )

        assert cfd.options == []

    def test_options_for_select(self):
        """Test options for select field."""
        cfd = CustomFieldDefinitionFactory(
            field_type=CustomFieldDefinition.FieldType.SELECT,
            options=["Low", "Medium", "High"],
        )

        assert cfd.options == ["Low", "Medium", "High"]

    def test_options_can_be_modified(self):
        """Test that options can be modified."""
        cfd = SelectCustomFieldDefinitionFactory()
        original_count = len(cfd.options)

        cfd.options.append("New Option")
        cfd.save()

        cfd.refresh_from_db()
        assert len(cfd.options) == original_count + 1


# =============================================================================
# CustomFieldDefinition String Representation Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldDefinitionStrRepresentation:
    """Tests for CustomFieldDefinition __str__ method."""

    def test_str_representation(self):
        """Test string representation includes name and type."""
        cfd = CustomFieldDefinitionFactory(
            name="Test Field",
            field_type=CustomFieldDefinition.FieldType.TEXT,
        )

        assert "Test Field" in str(cfd)
        assert "text" in str(cfd)


# =============================================================================
# CustomFieldDefinition Ordering Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldDefinitionOrdering:
    """Tests for CustomFieldDefinition ordering."""

    def test_ordering_by_order_then_name(self):
        """Test that fields are ordered by order, then name."""
        cfd3 = CustomFieldDefinitionFactory(name="Charlie", order=2)
        cfd1 = CustomFieldDefinitionFactory(name="Zebra", order=1)
        cfd2 = CustomFieldDefinitionFactory(name="Alpha", order=1)

        fields = list(CustomFieldDefinition.objects.all())

        # Order 1 before Order 2, then alphabetically within same order
        assert fields[0].name == "Alpha"
        assert fields[1].name == "Zebra"
        assert fields[2].name == "Charlie"


# =============================================================================
# CustomFieldDefinition Required Field Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldDefinitionRequired:
    """Tests for CustomFieldDefinition is_required field."""

    def test_not_required_by_default(self):
        """Test that fields are not required by default."""
        cfd = CustomFieldDefinitionFactory()

        assert cfd.is_required is False

    def test_required_field(self):
        """Test creating a required field."""
        cfd = CustomFieldDefinitionFactory(is_required=True)

        assert cfd.is_required is True


# =============================================================================
# CustomFieldValue Creation Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldValueCreation:
    """Tests for CustomFieldValue model creation."""

    def test_create_text_value(self):
        """Test creating a text field value."""
        person = PersonFactory()
        definition = CustomFieldDefinitionFactory(
            field_type=CustomFieldDefinition.FieldType.TEXT,
        )

        value = CustomFieldValueFactory(
            person=person,
            definition=definition,
            value="Reading, hiking, cooking",
        )

        assert value.person == person
        assert value.definition == definition
        assert value.value == "Reading, hiking, cooking"

    def test_create_number_value(self):
        """Test creating a number field value."""
        definition = NumberCustomFieldDefinitionFactory()
        value = CustomFieldValueFactory(
            definition=definition,
            value=42,
        )

        assert value.value == 42

    def test_create_date_value(self):
        """Test creating a date field value."""
        definition = DateCustomFieldDefinitionFactory()
        value = CustomFieldValueFactory(
            definition=definition,
            value="2023-12-25",
        )

        assert value.value == "2023-12-25"

    def test_create_select_value(self):
        """Test creating a select field value."""
        definition = SelectCustomFieldDefinitionFactory()
        value = CustomFieldValueFactory(
            definition=definition,
            value="Option 1",
        )

        assert value.value == "Option 1"

    def test_create_multiselect_value(self):
        """Test creating a multi-select field value."""
        definition = MultiSelectCustomFieldDefinitionFactory()
        value = CustomFieldValueFactory(
            definition=definition,
            value=["Choice A", "Choice C"],
        )

        assert value.value == ["Choice A", "Choice C"]


# =============================================================================
# CustomFieldValue Constraints Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldValueConstraints:
    """Tests for CustomFieldValue constraints."""

    def test_unique_per_person(self):
        """Test that each person can only have one value per field definition."""
        person = PersonFactory()
        definition = CustomFieldDefinitionFactory()

        CustomFieldValue.objects.create(
            person=person,
            definition=definition,
            value="First value",
        )

        with pytest.raises(IntegrityError):
            CustomFieldValue.objects.create(
                person=person,
                definition=definition,
                value="Second value",
            )

    def test_different_persons_same_field(self):
        """Test that different persons can have same field."""
        person1 = PersonFactory()
        person2 = PersonFactory()
        definition = CustomFieldDefinitionFactory()

        cfv1 = CustomFieldValue.objects.create(
            person=person1,
            definition=definition,
            value="Value 1",
        )
        cfv2 = CustomFieldValue.objects.create(
            person=person2,
            definition=definition,
            value="Value 2",
        )

        assert cfv1.pk != cfv2.pk


# =============================================================================
# CustomFieldValue String Representation Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldValueStrRepresentation:
    """Tests for CustomFieldValue __str__ method."""

    def test_str_representation(self):
        """Test string representation includes person and field name."""
        person = PersonFactory(first_name="John", last_name="Doe")
        definition = CustomFieldDefinitionFactory(name="Favorite Color")
        value = CustomFieldValueFactory(
            person=person,
            definition=definition,
            value="Blue",
        )

        str_rep = str(value)
        assert "John Doe" in str_rep
        assert "Favorite Color" in str_rep


# =============================================================================
# CustomFieldValue Cascade Delete Tests
# =============================================================================


@pytest.mark.django_db
class TestCustomFieldValueCascadeDelete:
    """Tests for CustomFieldValue cascade delete behavior."""

    def test_delete_person_deletes_values(self):
        """Test that deleting person deletes their custom field values."""
        person = PersonFactory()
        definition = CustomFieldDefinitionFactory()
        value = CustomFieldValueFactory(person=person, definition=definition)
        value_id = value.pk

        person.delete()

        assert not CustomFieldValue.objects.filter(pk=value_id).exists()

    def test_delete_definition_deletes_values(self):
        """Test that deleting definition deletes all its values."""
        definition = CustomFieldDefinitionFactory()
        value1 = CustomFieldValueFactory(definition=definition)
        value2 = CustomFieldValueFactory(definition=definition)
        value_ids = [value1.pk, value2.pk]

        definition.delete()

        assert not CustomFieldValue.objects.filter(pk__in=value_ids).exists()


# =============================================================================
# Person CustomFieldValue Relationship Tests
# =============================================================================


@pytest.mark.django_db
class TestPersonCustomFieldValueRelationship:
    """Tests for Person-CustomFieldValue relationship."""

    def test_person_custom_field_values(self):
        """Test getting all custom field values for a person."""
        person = PersonFactory()
        def1 = CustomFieldDefinitionFactory(name="Field 1")
        def2 = CustomFieldDefinitionFactory(name="Field 2")

        cfv1 = CustomFieldValueFactory(person=person, definition=def1)
        cfv2 = CustomFieldValueFactory(person=person, definition=def2)

        assert person.custom_field_values.count() == 2
        assert cfv1 in person.custom_field_values.all()
        assert cfv2 in person.custom_field_values.all()

    def test_definition_values_relationship(self):
        """Test getting all values for a definition."""
        definition = CustomFieldDefinitionFactory()
        person1 = PersonFactory()
        person2 = PersonFactory()

        cfv1 = CustomFieldValueFactory(person=person1, definition=definition)
        cfv2 = CustomFieldValueFactory(person=person2, definition=definition)

        assert definition.values.count() == 2
        assert cfv1 in definition.values.all()
        assert cfv2 in definition.values.all()
