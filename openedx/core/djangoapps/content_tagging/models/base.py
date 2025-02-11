"""
Content Tagging models
"""
from __future__ import annotations

from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext as _
from openedx_tagging.core.tagging.models import Taxonomy
from organizations.models import Organization


class TaxonomyOrg(models.Model):
    """
    Represents the many-to-many relationship between Taxonomies and Organizations.

    We keep this as a separate class from ContentTaxonomy so that class can remain a proxy for Taxonomy, keeping the
    data models and usage simple.
    """

    class RelType(models.TextChoices):
        OWNER = "OWN", _("owner")

    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.CASCADE)
    org = models.ForeignKey(
        Organization,
        null=True,
        default=None,
        on_delete=models.CASCADE,
        help_text=_(
            "Organization that is related to this taxonomy."
            "If None, then this taxonomy is related to all organizations."
        ),
    )
    rel_type = models.CharField(
        max_length=3,
        choices=RelType.choices,
        default=RelType.OWNER,
    )

    class Meta:
        indexes = [
            models.Index(fields=["taxonomy", "rel_type"]),
            models.Index(fields=["taxonomy", "rel_type", "org"]),
        ]

    @classmethod
    def get_relationships(
        cls, taxonomy: Taxonomy, rel_type: RelType, org_short_name: str | None = None
    ) -> QuerySet:
        """
        Returns the relationships of the given rel_type and taxonomy where:
        * the relationship is available for all organizations, OR
        * (if provided) the relationship is available to the org with the given org_short_name
        """
        # A relationship with org=None means all Organizations
        org_filter = Q(org=None)
        if org_short_name is not None:
            org_filter |= Q(org__short_name=org_short_name)
        return cls.objects.filter(
            taxonomy=taxonomy,
            rel_type=rel_type,
        ).filter(org_filter)

    @classmethod
    def get_organizations(
        cls, taxonomy: Taxonomy, rel_type: RelType
    ) -> list[Organization]:
        """
        Returns the list of Organizations which have the given relationship to the taxonomy.
        """
        rels = cls.objects.filter(
            taxonomy=taxonomy,
            rel_type=rel_type,
        )
        # A relationship with org=None means all Organizations
        if rels.filter(org=None).exists():
            return list(Organization.objects.all())
        return [rel.org for rel in rels]
