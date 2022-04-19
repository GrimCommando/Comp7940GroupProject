FROM python:latest
RUN mkdir /app
WORKDIR /app
COPY chatbot.py /app
COPY requirements.txt /app
RUN pip install pip update
RUN pip install -r requirements.txt
ENV ACCESS_TOKEN=5254405134:AAE54_WW-cyvoDTvrBGpzIxbbGB7a6jDydA
ENV HOST=redis-15965.c290.ap-northeast-1-2.ec2.cloud.redislabs.com
ENV PASSWORD=cCLE1L7dQcXu8gB4aJ9zgxEJjPMTu6ML
ENV REDISPORT=15965
CMD python /app/chatbot.py

#ENTRYPOINT python /app/chatbot.py