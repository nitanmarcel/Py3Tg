import asyncio
import html
import json
import logging
import re
import os
import shutil
import epicbox

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from config import API_HASH, API_ID, BOT_TOKEN, MAX_CONTAINERS
from telethon import TelegramClient, events
from telethon.tl.custom import Button

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TelegramClient(None, API_ID, API_HASH)
client.parse_mode = 'html'

if not bool(shutil.which('docker')):
    logger.error(
        "Docker is not installed. Please first install it using your system's package manager then run this script again!")
    quit(0)

else:
    import docker
    from docker.errors import DockerException
    logger.info("Pulling the latest docker image.")
    try:
        docker.from_env().images.pull("nitanmarcel/py3tg:latest")
    except DockerException as docker_exc:
        logger.error(
            "Failed to pull the latest docker image. Make sure docker is up and running then try again: " + str(docker_exc))
        quit(0)


loop = asyncio.get_event_loop()
thread_pool = ThreadPoolExecutor(max_workers=None)

semaphore = None
if MAX_CONTAINERS > 0:
    semaphore = asyncio.Semaphore(MAX_CONTAINERS)


profiles_json_source = 'profiles.json'
if not os.path.isfile(profiles_json_source):
    profiles_json_source = 'profiles_example.json'

with open(profiles_json_source, 'r+') as profile_js:
    jsondata = ''.join(
        line for line in profile_js if not line.startswith('//'))
    profiles = json.loads(jsondata)
    if profiles_json_source.split("_", 1)[-1] == 'example.json':
        profiles = {'default': profiles['default']}


epicbox.configure(
    profiles=[epicbox.Profile(name, 'nitanmarcel/py3tg:latest', **profile['profile'])
              for name, profile in profiles.items()])


async def _uexec(code, profile='default'):
    files = [{'name': 'main.py', 'content': str.encode(code)}]
    if profile not in profiles.keys():
        profile = 'default'
    result = await loop.run_in_executor(executor=thread_pool, func=partial(epicbox.run, profile, 'if type pypy3 >/dev/null 2>&1; then pypy3 main.py; else python main.py; fi', files=files, limits=profiles[profile]['limits']))
    return result


async def uexec(code, profile='default'):
    if semaphore:
        async with semaphore:
            return await _uexec(code, profile)
    return await _uexec(code, profile)


def _format_result(result):
    stdout = result['stdout'].decode()
    stderr = result['stderr'].decode()
    duration = result['duration']
    exit_code = result['exit_code']
    timeout = result['timeout']
    oom_killed = result['oom_killed']

    success = stdout or not any(
        (stderr, timeout, oom_killed,))

    result_template = '<b>Result:</b>\n<pre>{result}</pre>'
    error_template = '<b>Error:</b>\n<pre>{error}</pre>'

    if stdout and not stderr:
        stdout = result_template.format(result=html.escape(stdout))
    elif stderr and not stdout:
        stderr = error_template.format(error=html.escape(stderr))
    elif stderr and stdout:
        stdout = result_template.format(
            result=html.escape(stdout) + '\n' + html.escape(stderr))
    else:
        if timeout:
            stderr = error_template.format(
                error='RuntimeError: Execution took longer than excepted.')
        elif oom_killed:
            stderr = error_template.format(
                error='RuntimeError: Memory threshold exceeded.')

    return stdout or stderr, success, duration, exit_code, timeout, oom_killed


async def main():
    await client.start(bot_token=BOT_TOKEN)
    async with client:
        me = await client.get_me()

        start_regex = re.compile(rf'^/start|^/start@{me.username}')
        exec_regex = re.compile(r'^/exec([\s\S]*)?')

        stats = {}

        @client.on(events.NewMessage(outgoing=False, incoming=True, pattern=start_regex))
        async def _start(event):
            await event.reply(f'Use <code>/exec {html.escape("<python-code-here>")}</code> to give me some python code to execute.')

        @client.on(events.NewMessage(outgoing=False, incoming=True, pattern=exec_regex))
        async def _exec(event):
            msg = event.message
            code = event.pattern_match.group(1)
            if not code:
                await event.reply(f'Use <code>/exec {html.escape("<python-code-here>")}</code> to give me some python code to execute.')
                return
            code = code.lstrip()
            stats_id = str(msg.id) + str(event.chat_id)

            result = await uexec(code, profile=str(event.sender_id))
            parsed_result, status, duration, exit_code, timeout, oom_killed = _format_result(
                result)

            stats[stats_id] = {'exit_code': exit_code, 'duration': duration,
                               'timeout': timeout, 'oom_killed': oom_killed}

            result = f'<b>Code:</b>\n<pre>{code}</pre>\n\n' + parsed_result
            if len(result) < 4096:
                await event.reply(result, buttons=[Button.inline('Stats', data=stats_id)])
            else:
                await event.reply('Error: Message length exceeded telegram\'s limits.')

        @client.on(events.InlineQuery())
        async def _inline_exec(event):
            code = event.text.lstrip()
            if code:
                stats_id = str(event.id) + str(event.chat_id)
                result = await uexec(code, profile=str(event.sender_id))
                parsed_result, status, duration,  exit_code, timeout, oom_killed = _format_result(
                    result)

                stats[stats_id] = {'exit_code': exit_code, 'duration': duration,
                                   'timeout': timeout, 'oom_killed': oom_killed}

                builder = event.builder

                result = f'<b>Code:</b>\n<pre>{code}</pre>\n\n' + parsed_result

                if len(result) < 4096:
                    await event.answer([
                        builder.article('Success' if status else 'Error', text=result, buttons=[
                                        Button.inline('Stats', data=stats_id)], parse_mode='html')
                    ],
                        cache_time=0)
                else:
                    await event.answer([
                        builder.article('Message length exceeded telegram\'s limits.', text='Error: Message length exceeded telegram\'s limits.', buttons=[
                                        Button.inline('Stats', data=stats_id)], parse_mode='html')
                    ],
                        cache_time=0)

        @client.on(events.CallbackQuery())
        async def _stats(event):
            data = event.data.decode()
            if data in stats.keys():
                stats_ = stats[data]
                stats_msg = ''
                for k, v in stats_.items():
                    stats_msg += k.replace('_', ' ').title() + \
                        ': ' + str(v) + '\n'
                await event.answer(stats_msg, cache_time=0, alert=True)

        await client.run_until_disconnected()

if __name__ == '__main__':
    loop.run_until_complete(main())
