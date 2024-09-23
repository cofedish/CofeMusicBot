FROM ubuntu

# Обновляем пакеты и устанавливаем необходимые инструменты
RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y build-essential unzip software-properties-common shadowsocks-libev git ffmpeg libopus-dev libffi-dev libsodium-dev python3-pip python3-venv
RUN apt-get install -y proxychains
COPY proxychains.conf /etc/proxychains.conf

# Создаем виртуальное окружение и активируем его
RUN python3 -m venv /app/venv

# Активируем виртуальное окружение и устанавливаем pip в нем
RUN /app/venv/bin/pip install --upgrade pip

# Копируем файл зависимостей и устанавливаем Python-библиотеки в виртуальное окружение
COPY requirements.txt /app/requirements.txt
RUN /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Копируем весь проект в контейнер
COPY . /app

# Создаем конфигурационный файл Shadowsocks в директории /app
RUN echo '{ \
    "server": "93.113.180.22", \
    "server_port": 8388, \
    "local_port": 1080, \
    "password": "ZrwbrYgNZEVW", \
    "timeout": 600, \
    "method": "aes-128-gcm" \
}' > /app/config.json

# Устанавливаем рабочую директорию
WORKDIR /app

# Команда запуска Shadowsocks и бота с активацией виртуального окружения
CMD proxychains /app/venv/bin/python /app/main.py

