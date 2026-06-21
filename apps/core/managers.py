"""Managers and querysets implementing OpenMRS-style soft deletion.

OpenMRS never hard-deletes clinical or metadata records. Instead it marks
transactional data as *voided* and metadata as *retired*. These managers make
the "active" (non-voided / non-retired) records the default working set while
still allowing access to the full table when auditing or restoring.
"""
from django.db import models


class VoidableQuerySet(models.QuerySet):
    """Queryset for transactional ``BaseOpenmrsData`` models."""

    def active(self):
        return self.filter(voided=False)

    def voided(self):
        return self.filter(voided=True)


class RetireableQuerySet(models.QuerySet):
    """Queryset for metadata ``BaseOpenmrsMetadata`` models."""

    def active(self):
        return self.filter(retired=False)

    def retired(self):
        return self.filter(retired=True)


class VoidableManager(models.Manager):
    """Default manager that hides voided rows."""

    def get_queryset(self):
        return VoidableQuerySet(self.model, using=self._db).active()


class RetireableManager(models.Manager):
    """Default manager that hides retired rows."""

    def get_queryset(self):
        return RetireableQuerySet(self.model, using=self._db).active()
