#!/usr/bin/env python
"""
Запуск Django dev-сервера с HTTPS для локальной разработки.
Использует mkcert-сертификаты.
"""
import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djilab.settings")

    from django.core.servers.basehttp import get_internal_wsgi_application
    from werkzeug.serving import run_simple

    application = get_internal_wsgi_application()

    cert_file = "192.168.0.107+2.pem"
    key_file = "192.168.0.107+2-key.pem"

    print("🔐 Запуск HTTPS-сервера на https://0.0.0.0:8000")
    print(f"📜 Сертификат: {cert_file}")

    run_simple(
        "0.0.0.0",
        8000,
        application,
        use_reloader=True,
        use_debugger=True,
        ssl_context=(cert_file, key_file),
        threaded=True,
    )
