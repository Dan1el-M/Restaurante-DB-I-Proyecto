FROM python:3.14-slim

WORKDIR /backend

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./backend .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]