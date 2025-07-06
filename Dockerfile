FROM python:3.12-slim

#Create work directory and copy content
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

#Install app requirements 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app


#Run the code
CMD ["fastapi", "run", "app/main.py", "--port", "3000"]
