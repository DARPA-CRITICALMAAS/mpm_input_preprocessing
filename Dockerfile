FROM python:3.11
RUN apt update 
RUN apt -y install libgdal-dev 

RUN apt-get install -y --no-install-recommends libgl1-mesa-glx

ENV PATH=/home/apps/bin:/home/apps/.local/bin:$PATH

COPY . /home/apps/mpm_input_preprocessing

RUN useradd --user-group --create-home apps
RUN chown -v -R apps:apps /home/apps

USER apps
WORKDIR /home/apps/mpm_input_preprocessing

RUN pip install --upgrade pip --user
RUN pip install --user /home/apps/mpm_input_preprocessing

CMD ["uvicorn", "mpm_input_preprocessing.http.api:api", "--host", "0.0.0.0", "--port", "8082", "--log-config", "logging.yaml", "--workers", "1", "--reload"]
