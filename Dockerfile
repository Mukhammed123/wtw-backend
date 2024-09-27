FROM python:3.10

WORKDIR /
ADD ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt
ADD . /
EXPOSE 8033
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8033"]