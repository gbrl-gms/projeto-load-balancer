FROM python:3.9-slim
RUN pip install flask psutil
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]