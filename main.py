import requests
import os
import pytz
from datetime import datetime, timedelta
import random
import datetime as dt


userName = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
studentId = os.getenv('STUDENTID')


loginUrl = 'https://portal.yamagata-u.ac.jp/Account/Login?ReturnUrl=%2F'
studyTimesUrl = 'https://portal.yamagata-u.ac.jp/SelfStudy/StudyTimes'


def post(url,
         loginPostCookies, 
         studentId, 
         typeId, 
         startTime, 
         endTime):
   
   if(typeId <= 0 or typeId > 6 or typeId == 3):
      raise Exception("Invild type id")

   timeFormat = '%Y-%m-%dT%H:%M:%S.000Z'

   startTime = (startTime + timedelta(hours = -9)).strftime(timeFormat)
   endTime = (endTime + timedelta(hours = -9)).strftime(timeFormat)
   

   postData = {
               "StudentId": studentId,
               "TypeId": typeId,
               "StartDate": startTime,
               "EndDate": endTime
              }

   print(postData)

   requests.post(url, 
                 json = postData,
                 cookies = loginPostCookies,
                 verify = False)
   
   return


requests.packages.urllib3.disable_warnings()
loginGet = requests.get(loginUrl,
                        verify=False)

requestToken = loginGet.cookies.get_dict()['__RequestVerificationToken']

loginPostData = {
                  '__RequestVerificationToken': requestToken,
                  'Email': userName,
                  'Password': password,
                  'RememberMe': 'false',
                  'device_id': ''
                }

loginPost = requests.post(loginUrl, 
                          json = loginPostData,
                          cookies = loginGet.cookies,
                          verify = False)
loginPostCookies = loginPost.history[0].cookies


now = datetime.now(tz = pytz.timezone('Asia/Tokyo'))

currentMidnight = dt.datetime(
    now.year, 
    now.month, 
    now.day)


sleepMorning = random.randrange(6,8)
sleepNight = random.randrange(1,2)

empty1 = random.randrange(0,3)
empty2 = random.randrange(0,3)
empty3 = random.randrange(0,3)

studySelf1 = random.randrange(1,3)
studySelf2 = random.randrange(1,3)
circle = random.randrange(2,4)

otherStudy = 24 - sleepMorning - sleepNight - studySelf1 - studySelf2 - empty1 - empty2 - empty3 - circle

activityList = [
   {'TypeId':6,'During':sleepMorning},
   {'TypeId':999,'During':empty1},
   {'TypeId':1,'During':studySelf1},
   {'TypeId':999,'During':empty2},
   {'TypeId':2,'During':otherStudy},
   {'TypeId':999,'During':empty3},
   {'TypeId':4,'During':circle},
   {'TypeId':1,'During':studySelf2},
   {'TypeId':6,'During':sleepNight},
]

arrangementDuring = 0

for activity in activityList:
   during = activity['During'] 
   typeId = activity['TypeId']
   if(during == 0):
      continue

   startTime = currentMidnight + timedelta(hours = arrangementDuring)
   endTime = startTime + timedelta(hours = during)

   arrangementDuring += during

   if(typeId == 999):
      continue

   post(studyTimesUrl,
        loginPostCookies,
        studentId, 
        typeId, 
        startTime, 
        endTime)


