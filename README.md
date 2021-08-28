# Py3Tg
Execute python3 code directly from telegram using a docker sandbox. The bot can be found on telegram [here](t.me/py3tg_bot) but you can also self host it using the instructions below.

### Self Hosting

* Requirements
  - docker
  - python3

* Installation
  - git clone this repo using `git clone https://github.com/nitanmarcel/Py3Tg`
  - cd to the clone repo using `cd Py3Tg`
  - build the base docker image using `docker build . -t pytg` (The tag of the container needs to be pytg, do not change that unless you've changed it in the `main.py` file.
  - configure your telegram app id, app hash and bot token by making a copy of the `example_config.py` file, renaming it to `config.py` and editing the variables inside the file. DO NOT EDIT THE VARIABLES INSIDE EXAMPLE_CONFIG.PY FILE!!!
  - run the bot using `python3 main.py`
  
* Configure profiles/permissions
- All the profiles and user permissions inside the docker container are controlled by the `profiles.json` file:
  - user: What user will the code executed by an user will be used inside the docker container. It can be `sandbox` or `root`.
  - network_disabled: Either if the container will have access to a network connection or not.
  - cputime: CPU time in seconds, `null` for unlimited.
  - realtime: Real time in seconds, `null for unlimited.
  - memory: Memory in megabytes, `null` for unlimited
  - processes: Limit the max processes the sandbox can have. -1 or `null` for unlimited.
