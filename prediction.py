import csv_io
import httplib2
import sys
import traceback
#import time

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

FLOW = OAuth2WebServerFlow(
    client_id='',
    client_secret='',
    scope='https://www.googleapis.com/auth/prediction',
    user_agent='prediction-cmdline-sample/1.0')



def main():

    #Auth
    storage = Storage('prediction.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid: credentials = run(FLOW, storage) 
    http = httplib2.Http()
    http = credentials.authorize(http)
    
    service = build("prediction", "v1.4", http=http)

    testset = csv_io.read_csv("test.csv", False)
    submit = []
    count = 1
    for i in range(len(testset)):
        try:
            body = {"input":{"csvInstance":parseInput(testset[i])}}
            prediction = service.trainedmodels().predict(id="br2", body=body).execute()
            predval = prediction['outputValue']
            #Google Predict isn't smart enough to figure out that we want a probability
            #Instead it fits a regression, which can go outside the range 0-1
            if predval >=1.0: predval = 0.99999
            if predval <=0.0: predval = 0.00001
            
            submit.append(predval)
            print str(count) + ": " + str(predval)
        except AccessTokenRefreshError:
            print ("The credentials have been revoked or expired, please re-run the application to re-authorize")
        except:
            etype, value, tb = sys.exc_info()
            msg = ''.join(traceback.format_exception(etype, value, tb))
            csv_io.write_csv("g_submit_err.csv", [["%f" % x] for x in submit])
            print "error on: " + str(i) + "  exception: " + msg
        if count % 50 == 0:
            csv_io.write_csv("g_submit.csv", [["%f" % x] for x in submit])
            print "wrote to disk"
        count = count + 1
        #uncomment below if hitting throttling limites from Google
        #time.sleep(0.5)
    csv_io.write_csv("g_submit.csv", [["%f" % x] for x in submit])

#turns numeric strings into floats - google predict api balks at numbers passed as strings
def parseInput(row):
    ret = []
    for i in row:
        try:
            ret.append(float(i))
        except ValueError:
            ret.append(i)
    return ret

def read_csv(file_path, has_header = True):
    with open(file_path) as f:
        if has_header: f.readline()
        data = []
        for line in f:
            line = line.strip().split(",")
            data.append([x for x in line])
    return data

def write_csv(file_path, data):
    with open(file_path,"w") as f:
        for line in data: f.write(",".join(line) + "\n")

if __name__ == '__main__':
    main()
