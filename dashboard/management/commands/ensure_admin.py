import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создаёт staff-пользователя из переменных окружения, если его ещё нет"

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@localhost")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Пользователь {username} уже есть.")
            return
        if not password:
            self.stderr.write("Задайте DJANGO_SUPERUSER_PASSWORD в .env")
            return
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Создан администратор {username}"))
