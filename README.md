# Py3Tg
Execute python3 code using [pypy3](https://www.pypy.org/features.html) directly from telegram using a docker sandbox. The bot can be found on telegram [here](https://t.me/py3tg_bot) but you can also self-host it using the instructions below.

# WARNING ⚠️: I'm not responsible if your system gets destroyed somehow while self-hosting this bot. In theory, this should be secured as long as you don't give root permissions to random telegram users in the `profiles.json` file. Docker still has its flaws, make sure you're running this on a VPS where you have nothing to lose,  don't connect to your VPS as a root user or any user that doesn't have a sudo password.
### Self Hosting

* Requirements
  - docker
  - python3

* Installation
  - git clone this repo using `git clone https://github.com/nitanmarcel/Py3Tg`
  - cd to the cloned repo using `cd Py3Tg`
  - configure your telegram app id, app hash, and bot token by making a copy of the `example_config.py` file, renaming it to `config.py`, and editing the variables inside the file. DO NOT EDIT THE VARIABLES INSIDE THE EXAMPLE_CONFIG.PY FILE!!!
  - run the bot using `python3 main.py`
  
* Configure profiles/permissions
- All the profiles and user permissions inside the docker container are controlled by the `profiles.json` file. Copy the `profiles_example.json` file to `profiles.json` and edit it to your liking:
  - user: What user will the code executed by a user will be used inside the docker container. It can be `sandbox` or `root`.
  - network_disabled: Either if the container will have access to a network connection or not.
  - cputime: CPU time in seconds, `null` for unlimited.
  - realtime: Real time in seconds, `null` for unlimited.
  - memory: Memory in megabytes, `null` for unlimited
  - processes: Limit the max processes the sandbox can have. `-1` or `null` for unlimited.
  - file_size: Limit the size of created files.


### How does it work:

Each time a script is sent to execution from telegram, the bot creates a new docker container in which it executes the code then it destroys the container after its job is done.
One container has around 40MB due to its dependencies and each time a container is created around 40MB of storage memory will be assigned to it until the execution is over and the container gets destroyed. Note that creating big files inside the containers might increase its size, but this should never happen if the default settings are kept.


To limit the storage usage on your VPS/servers you should:
- Keep the maximum allowed CPU time, real-time, and memory in the profiles configuration mentioned in the section above at a low value. These should prevent the container to stack up and increase your storage usage.
- Keep the maximum allowed file size to a low value to prevent big files from being created in the container.
- Set how many containers can run at once in the config.py file. To calculate what value you should use for its limit, take your VPS free storage, or the storage you want to assign to this bot and multiply it with 40 or higher, depending on your limits mentioned above. Once the limit of containers is reached the script will wait for a container to be destroyed before creating a new one.