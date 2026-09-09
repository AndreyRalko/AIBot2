"""Production WSGI server (Waitress)."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application
from waitress import serve

application = get_wsgi_application()


def main():
    listen = os.environ.get("WAITRESS_LISTEN", "0.0.0.0:8000")
    host, _, port = listen.rpartition(":")
    if not host or not port:
        host, port = "0.0.0.0", "8000"
    threads = int(os.environ.get("WAITRESS_THREADS", "6"))
    print(f"Waitress listening on {host}:{port}")
    serve(application, host=host, port=int(port), threads=threads, ident="aibot")


if __name__ == "__main__":
    main()
