FROM python:3.8

WORKDIR ./chatgpt

ADD . .

RUN pip3 install -r requirements.txt

EXPOSE 52712

RUN /bin/cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' > /etc/timezone

CMD ["python", "main.py"]