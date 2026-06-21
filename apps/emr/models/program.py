"""Programs and enrolment -- longitudinal care (HIV, TB, ANC, NCD ...).

OpenMRS models care programs as a workflow/state machine. A patient is
*enrolled* in a program and moves through *states* within *workflows*.
"""
from django.db import models

from apps.core.models import BaseOpenmrsData, BaseOpenmrsMetadata


class Program(BaseOpenmrsMetadata):
    """A care program a patient can be enrolled in."""

    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="programs", null=True, blank=True
    )


class ProgramWorkflow(BaseOpenmrsMetadata):
    """A dimension of state within a program (e.g. Treatment Status)."""

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="workflows")


class ProgramWorkflowState(BaseOpenmrsMetadata):
    """A discrete state within a workflow (e.g. Active on ART, Transferred out)."""

    workflow = models.ForeignKey(
        ProgramWorkflow, on_delete=models.CASCADE, related_name="states"
    )
    initial = models.BooleanField(default=False)
    terminal = models.BooleanField(default=False)


class PatientProgram(BaseOpenmrsData):
    """A patient's enrolment in a program."""

    patient = models.ForeignKey(
        "emr.Patient", on_delete=models.CASCADE, related_name="program_enrolments"
    )
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="enrolments")
    location = models.ForeignKey(
        "emr.Location", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    date_enrolled = models.DateField(db_index=True)
    date_completed = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["patient", "program"])]


class PatientState(BaseOpenmrsData):
    """A period during which an enrolment is in a particular state."""

    patient_program = models.ForeignKey(
        PatientProgram, on_delete=models.CASCADE, related_name="states"
    )
    state = models.ForeignKey(
        ProgramWorkflowState, on_delete=models.PROTECT, related_name="patient_states"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)


class ConceptStateConversion(BaseOpenmrsData):
    """Auto-transition a program enrolment when a triggering obs is recorded.

    Mirrors OpenMRS ``ConceptStateConversion``: e.g. "when the concept
    'Patient died' is observed, move the workflow to the 'Died' state". This is
    what lets observations drive program state changes automatically.
    """

    concept = models.ForeignKey(
        "emr.Concept", on_delete=models.PROTECT, related_name="state_conversions"
    )
    workflow = models.ForeignKey(
        ProgramWorkflow, on_delete=models.CASCADE, related_name="state_conversions"
    )
    state = models.ForeignKey(
        ProgramWorkflowState, on_delete=models.PROTECT, related_name="state_conversions"
    )

    class Meta:
        unique_together = ("concept", "workflow")

    def __str__(self):
        return f"{self.concept} -> {self.state}"
