import re
import random
import os
import os.path

token = os.getenv('TOKEN')
repo = os.getenv('GITHUB_REPOSITORY')
if not token or not repo:
    raise Exception('Add token and repo in github action secrets')

ymlPath = '.github/workflows/update.yml'

if not os.path.isfile(ymlPath):
    raise Exception(f'Lost file {ymlPath}')


def getScheduleFileContent() -> str:
    file = open(ymlPath, 'r')
    content = file.read()
    file.close()
    return content


def setScheduleFileContent(content: str):
    file = open(ymlPath, 'w')
    file.write(content)
    file.close()


def exeCommand(command):
    result = os.system(command)
    if result != 0:
        raise Exception(command)
    return


def updateSchedule(content: str, randomTime: str) -> str:
    content = re.sub(r'(?<=- cron:\s\').*(?=\')', randomTime, content)
    return content


def getRandomTime() -> str:
    randomHour = random.randint(1, 10)
    randomMinute = random.randint(0, 59)
    # UTC time 1-10 -> jp time 10-19
    randomTime = f'{randomMinute} {randomHour} * * *'
    return randomTime


def pushSchedule(time: str):
    if token and repo:
        exeCommand('git config --global user.email _@_.com')
        exeCommand('git config --global user.name CI')
        exeCommand('git add .')
        exeCommand(f'git commit -m "update schedule time -> {time}"')
        exeCommand(f'git push --set-upstream https://{token}@github.com/{repo} master:master')


def main():
    content = getScheduleFileContent()
    randomTime = getRandomTime()
    content = updateSchedule(content, randomTime)
    setScheduleFileContent(content)
    pushSchedule(randomTime)
    return


if __name__ == "__main__":
    main()
