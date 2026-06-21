"""Celery tasks for asynchronous analyzer message ingestion."""
from celery import shared_task


@shared_task
def ingest_analyzer_message_task(raw_payload, protocol="HL7", analyzer_id=None):
    """Ingest a raw analyzer transmission off the request path.

    Instrument middleware can fire-and-forget large batches here instead of
    blocking on the synchronous ingest endpoint.
    """
    from apps.lis.ingest import ingest_message
    from apps.lis.models import Analyzer

    analyzer = Analyzer.objects.filter(pk=analyzer_id).first() if analyzer_id else None
    message = ingest_message(raw_payload, protocol=protocol, analyzer=analyzer)
    return message.id
