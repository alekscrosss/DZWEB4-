FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 3000
ENV DATA_STORE=/data/data.json
CMD ["python", "./main.py"]