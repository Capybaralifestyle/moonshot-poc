FROM python:3.11-slim
WORKDIR /workspace

COPY requirements.txt .
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libjpeg-dev zlib1g-dev libopenjp2-7 curl \
 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://ollama.com/install.sh | sh
RUN pip install --no-cache-dir -r requirements.txt

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=agent123"]