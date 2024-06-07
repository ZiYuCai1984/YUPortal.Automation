import requests
import os
import re
import pytz
import random
import json
import datetime as dt
from urllib.parse import quote
from datetime import datetime, timedelta

userName = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

if not userName or not password:
    raise Exception('Add userName and password in github action secrets')

loginUrl = 'https://portal.yamagata-u.ac.jp/Account/Login?ReturnUrl=%2F'
studyTimesUrl = 'https://portal.yamagata-u.ac.jp/SelfStudy/StudyTimes'
portalHomePageUrl = 'https://portal.yamagata-u.ac.jp'

# noinspection PyRedeclaration,PyPep8Naming

requests.packages.urllib3.disable_warnings()


# noinspection PyPep8Naming
def postStudyRecord(loginPostCookies: any,
                    studentId: str,
                    typeId: int,
                    startTime: datetime,
                    endTime: datetime):
    if typeId <= 0 or typeId > 6 or typeId == 3:
        raise Exception("Invalid type id")

    if not studyTimesUrl or not loginPostCookies:
        raise Exception("Invalid argument")

    timeFormat = '%Y-%m-%dT%H:%M:%S.000Z'

    startTime = (startTime + timedelta(hours=-9)).strftime(timeFormat)
    endTime = (endTime + timedelta(hours=-9)).strftime(timeFormat)

    postData = {
        "StudentId": studentId,
        "TypeId": typeId,
        "StartDate": startTime,
        "EndDate": endTime
    }

    requests.post(url=studyTimesUrl,
                  json=postData,
                  cookies=loginPostCookies,
                  verify=False)

    return


def postLogin():
    loginGet = requests.get(loginUrl, verify=False)

    requestToken = loginGet.cookies.get_dict()['__RequestVerificationToken']

    loginPostData = {
        '__RequestVerificationToken': requestToken,
        'Email': userName,
        'Password': password,
        'RememberMe': 'false',
        'device_id': ''
    }

    loginData = requests.post(url=loginUrl,
                              json=loginPostData,
                              cookies=loginGet.cookies,
                              verify=False)
    loginPostCookies = loginData.history[0].cookies

    portalHomePage = requests.get(url=portalHomePageUrl,
                                  cookies=loginPostCookies,
                                  verify=False)

    studentId = re.search(r'(?<=studentId\s=\s\').*(?=\';)', portalHomePage.text).group(0)

    return loginPostCookies, requestToken, studentId


def newActivity(typeId: int, during: int):
    return {'TypeId': typeId, 'During': during}


def createActivityList(isWeekday: bool) -> list:
    if isWeekday:
        # !WARNING Bug, it needs to be in units of one hour
        sleepMorning = random.randint(6, 8)
        sleepNight = random.randint(1, 2)
        otherStudy1 = random.randint(0, 1)
        otherStudy2 = random.randint(0, 1)
        studySelf1 = random.randint(0, 1)
        studySelf2 = random.randint(0, 1)
        studySelf3 = random.randint(0, 1)
        circle = random.randint(0, 1)
    else:
        sleepMorning = random.randint(5, 7)
        sleepNight = random.randint(0, 2)
        otherStudy1 = random.randint(2, 3)
        otherStudy2 = random.randint(1, 2)
        studySelf1 = random.randint(0, 1)
        studySelf2 = random.randint(0, 1)
        studySelf3 = random.randint(0, 1)
        circle = random.randint(2, 4)

    activityList = [
        newActivity(1, studySelf1),
        newActivity(1, studySelf2),
        newActivity(1, studySelf3),
        newActivity(2, otherStudy1),
        newActivity(2, otherStudy2),
        newActivity(4, circle)
    ]

    leftTime = getLeftHours(activityList) - sleepMorning - sleepNight

    for i in range(leftTime):
        activityList.append(newActivity(999, 1))
    random.shuffle(activityList)

    activityList.insert(0, newActivity(6, sleepMorning))
    activityList.append(newActivity(6, sleepNight))
    return activityList


def getTokyoTime() -> datetime:
    return datetime.now(tz=pytz.timezone('Asia/Tokyo'))


def getLeftHours(activityList: list) -> int:
    leftHours = 24

    for activity in activityList:
        leftHours -= activity['During']

    if leftHours < 0:
        raise Exception(f"Invalid left hours {leftHours}")

    return leftHours


def getIsWeekday() -> bool:
    now = getTokyoTime().weekday()
    return now < 5


def getRandomMinutesTime(minutes: int) -> int:
    return random.randint(int(minutes / 6), minutes)


def getTimeListByActivityList(activityList: list):
    now = getTokyoTime()

    currentMidnight = dt.datetime(
        now.year,
        now.month,
        now.day)

    arrangementDuring = 0

    timeList = []

    for activity in activityList:
        during = activity['During']
        typeId = activity['TypeId']
        if during == 0:
            continue

        startTime = currentMidnight + timedelta(hours=arrangementDuring)
        endTime = startTime + timedelta(hours=during)

        arrangementDuring += during

        if typeId == 999:
            continue

        timeList.append((typeId, startTime, endTime))

    i = 0
    while i < len(timeList) - 1:
        typeId, startTime, endTime = timeList[i]
        typeIdNext, startTimeNext, endTimeNext = timeList[i + 1]
        if not startTimeNext.hour - endTime.hour <= 1:
            endTime = endTime + timedelta(minutes=random.randint(0, 5) * 10)
            startTimeNext = startTimeNext - timedelta(minutes=random.randint(0, 5) * 10)

            if endTime > startTimeNext:
                raise Exception(f"endTime {endTime} > startTimeNext {startTimeNext}")

            timeList[i] = (typeId, startTime, endTime)
            timeList[i + 1] = (typeIdNext, startTimeNext, endTimeNext)
        i += 1

    return timeList


def getTimeListByActivityListAndClassTimeList(activityList: list, classTimeList: list):
    currentHour = 0
    removePendingNum = len(classTimeList) * 2

    i = 0
    while i < len(activityList):
        during = activityList[i]['During']

        if not during == 0:
            currentHour += during

            if not len(classTimeList) == 0:
                # Need soft the time
                classObj = classTimeList[0]
                classTime = datetime.strptime(classObj['StartDate'], '%Y-%m-%dT%H:%M:%S')

                hour = classTime.hour
                if hour == 8:
                    # !WARNING 8:50->9:00
                    hour = 9

                if currentHour >= hour:
                    activityList.insert(i + 1, newActivity(3, 2))
                    classTimeList.remove(classObj)
        i += 1

    i = len(activityList) - 1
    while i >= 0:
        if removePendingNum == 0:
            break

        typeId = activityList[i]['TypeId']
        if typeId == 999:
            activityList.pop(i)
            removePendingNum -= 1
        i -= 1

    timeList = getTimeListByActivityList(activityList)

    i = len(timeList) - 1
    while i >= 0:
        if timeList[i][0] == 3:
            timeList.pop(i)
        i -= 1

    return timeList


def getClassTimeList(loginPostCookies: any,
                     studentId: str) -> list:
    timeFormat = '%Y-%m-%dT%H:%M:%S+09:00'
    safe = '/?=&'

    now = getTokyoTime()
    currentMidnight = quote(dt.datetime(
        now.year,
        now.month,
        now.day).strftime(timeFormat), safe)

    nextMidnight = quote(dt.datetime(
        now.year,
        now.month,
        now.day + 1).strftime(timeFormat), safe)

    currentStudyTimeUrl = f"{studyTimesUrl}?StudentId={studentId}&StartDate={currentMidnight}&EndDate={nextMidnight}"

    data = json.loads(requests.get(url=currentStudyTimeUrl,
                                   cookies=loginPostCookies,
                                   verify=False).content)

    classTimeList = []

    for item in data:
        if item['TypeId'] == 3:
            classTimeList.append({'StartDate': item['StartDate'], 'EndDate': item['EndDate']})

    return classTimeList


def main():
    isWeekday = getIsWeekday()
    activityList = createActivityList(isWeekday)

    loginPostCookies, requestToken, studentId = postLogin()

    if not isWeekday:
        timeList = getTimeListByActivityList(activityList)
    else:
        classTimeList = getClassTimeList(loginPostCookies=loginPostCookies,
                                         studentId=studentId)
        timeList = getTimeListByActivityListAndClassTimeList(activityList, classTimeList)

    for typeId, startTime, endTime in timeList:
        postStudyRecord(loginPostCookies=loginPostCookies,
                        studentId=studentId,
                        typeId=typeId,
                        startTime=startTime,
                        endTime=endTime)


if __name__ == "__main__":
    main()
