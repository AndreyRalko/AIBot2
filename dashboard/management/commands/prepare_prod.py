from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Миграции, collectstatic, администратор и проверка production-настроек"

    def handle(self, *args, **options):
        call_command("migrate", interactive=False)
        call_command("collectstatic", interactive=False, verbosity=1)
        call_command("ensure_admin")
        call_command("check", deploy=True)
        self.stdout.write(self.style.SUCCESS("Production-подготовка завершена."))
