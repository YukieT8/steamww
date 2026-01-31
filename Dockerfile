# Используем более современный образ Debian (Bullseye), где репозитории работают
FROM python:3.9-slim-bullseye

# Установка зависимостей для SteamCMD
# Мы добавляем архитектуру i386, так как SteamCMD — 32-битное приложение
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y \
    curl \
    lib32gcc-s1 \
    lib32stdc++6 \
    ca-certificates \
    && mkdir -p /root/steamcmd && cd /root/steamcmd \
    && curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf -

# Добавляем SteamCMD в PATH
ENV PATH="/root/steamcmd:${PATH}"

WORKDIR /app

# Копируем и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаем папку для шаблонов, если её нет
RUN mkdir -p /app/templates

# Запуск
CMD ["python", "app.py"]
