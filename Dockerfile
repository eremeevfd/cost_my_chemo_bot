FROM python:3.13.0a4-slim
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ./ /app/
CMD ["python", "main_fastapi.py"]
