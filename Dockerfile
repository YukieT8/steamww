FROM python:3.9-slim-buster

# Установка необходимых библиотек для SteamCMD (32-битные библиотеки обязательны)
RUN apt-get update && apt-get install -y \
    curl \
    lib32gcc1 \
    lib32stdc++6 \
    ca-certificates \
    && mkdir -p /root/steamcmd && cd /root/steamcmd \
    && curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf -

# Добавляем путь к steamcmd в системные переменные
ENV PATH="/root/steamcmd:${PATH}"

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы проекта
COPY . .

# Создаем папки для загрузок
RUN mkdir -p /app/downloads /app/templates

# Запуск приложения
CMD ["python", "app.py"]
