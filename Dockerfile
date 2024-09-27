FROM python:3.10

WORKDIR /app
ADD ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
ADD . /app
EXPOSE 8033
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8033"]