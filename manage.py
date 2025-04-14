#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import subprocess

class ReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"[WATCHDOG] Fichier modifié : {event.src_path}")
            os.execv(sys.executable, ['python'] + sys.argv)

def start_watchdog():
    event_handler = ReloadHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    print("[WATCHDOG] Surveillance du projet Django activée...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    # Démarrer le watchdog dans un thread séparé
    threading.Thread(target=start_watchdog, daemon=True).start()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ledjassa.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Assurez-vous qu'il est installé."
        ) from exc
    execute_from_command_line(sys.argv)






def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ledjassa.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
