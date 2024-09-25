from django.db.models.signals import post_migrate
from django.dispatch import receiver
from background_task.models import Task
from .tasks import geocode_imoveis

@receiver(post_migrate)
def schedule_geocode_tasks(sender, **kwargs):
    # Agende a task para rodar a cada hora
    geocode_imoveis(repeat=3600)
