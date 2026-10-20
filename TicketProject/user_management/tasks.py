from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.utils import timezone
from .models import Ticket


@shared_task(name="change_state")
def change_state():
    """Cancel unfinished tickets whose due date has passed; return count."""
    today = timezone.localdate()
    return Ticket.objects.filter(
        end_date__lt=today,
    ).exclude(
        state__in=(Ticket.DONE, Ticket.CANCEL),
    ).update(state=Ticket.CANCEL)

