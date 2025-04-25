# Используем полный Debian-образ Python, а не slim
FROM python:3.13

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы с зависимостями
COPY requirements.txt /app/requirements.txt
COPY .env /app/.env

# Обновляем pip и устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY ./app /app

# Запуск приложения
CMD ["python", "main.py"]