./stop.sh

nohup python -u bin/stream.py &
nohup python -u bin/expand_urls.py &
nohup python -u bin/expand_urls.py &
