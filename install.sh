python3 -m venv env;
source env/bin/activate;
pip install -r requirements.txt;
pip install -r requirements-dev.txt;
webdrivermanager firefox --linkpath "$(pwd)/env/bin";
