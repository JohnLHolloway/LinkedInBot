FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py config.py prompts.py image_gen.py rate_limit.py ./
COPY commands/ ./commands/
COPY config/ ./config/
CMD ["python", "bot.py"]
