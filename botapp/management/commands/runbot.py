from django.core.management.base import BaseCommand

from botapp.runner import run


class Command(BaseCommand):
    help = "Запуск Telegram-бота (long polling)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Telegram-бот запущен. Ctrl+C для остановки."))
        run()
