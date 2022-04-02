"""In this version of the server main replica resets when another client connects """
from multiprocessing import connection
import rpyc
from rpyc.utils.server import ThreadedServer,OneShotServer
import datetime
date_time=datetime.datetime.now()

from threading import Lock
import time
from functools import wraps
import sys
import datetime
import _thread
import time
import random

mutex=Lock()
# global variables
t=None

TIMESTAMP=0
otherProcessPorts=[]
messageTracker=[]
thisPort=int(sys.argv[1])
okCount=0


HELD="HELD"
DONOTWANT="DO-NOT-WANT"
WANTED="WANTED"
# start the main loop
running = True

class Process:

    def __init__(self, passiveTime=5,criticalSectionTime=10):
        self.state=DONOTWANT
        self.passiveTime = passiveTime
        self.criticalSectionTime=criticalSectionTime
        self.responses=[]


    # starts a thread that runs the process
    def start(self):
        _thread.start_new_thread(self.run, ())
    def updateData(self):
        self.data=self.setData
    def changeStateActive(self):
        mutex.acquire()
        self.state=HELD
        mutex.release()

    def changeStatePassive(self):
        mutex.acquire()
        self.state=DONOTWANT
        mutex.release()

    def changeStateWant(self):
        mutex.acquire()
        self.state="want"
        mutex.release()

    def changeStateWanting(self):
        mutex.acquire()
        self.state="wanting"
        mutex.release()

    def sendRequestCriticalSection(self):
        global okCount                
        global TIMESTAMP

        for conn in connections:
            res=conn.root.requestCriticalSection(TIMESTAMP,thisPort)
            print(res)
            if(res=="OK"):
                mutex.acquire()

                okCount+=1
                TIMESTAMP+=1
                
                mutex.release()

    def sendACK(self,connections):
        global messageTracker
        global otherProcessPorts
        global okCount
        global TIMESTAMP

        print(f"MessageTracer: {messageTracker} thisport: {thisPort}, type: {type(otherProcessPorts)}")

        for port in messageTracker:
            index=otherProcessPorts.index(port)
            conn=connections[index]
            conn.root.ack(thisPort)
            
            mutex.acquire()
            TIMESTAMP+=1
            mutex.release()

        mutex.acquire()
        messageTracker=[]
        okCount=0
        mutex.release()

    def stop(self):
        _thread.exit()

    def set_Data(self,newData):
        self.setData=newData
        
    def run(self):
        # updating data with cache time
        global okCount
        global otherProcessPorts

        while True:
            if self.state==DONOTWANT:
                randomWait=random.randrange(5,15)

                time.sleep(randomWait)

                self.changeStateWanting()

            elif(self.state==HELD):
                randomWait=random.randrange(10,15)
                
                time.sleep(randomWait)
                self.sendACK(connections)

                self.changeStatePassive()

            elif(self.state=="wanting"):

                self.sendRequestCriticalSection()

                self.changeStateWant()
            
            if(self.state=="want"):
                mutex.acquire()
                
                if(okCount>=len(otherProcessPorts)):
                    mutex.release()
                    self.changeStateActive()
                    continue

                mutex.release()


def cache(replicas:list,time):
    for p in replicas:
        p.cacheTime=time
    print(f"Cache time for update: {time}")





thread=Process()
thread.start()
connections=[]


# start a separate thread for system tick

class ProcessService(rpyc.Service):
    def exposed_other_ps_ports(self,ports):
        global otherProcessPorts
        global connections
        for port in ports:
            otherProcessPorts.append(port)
        for port in otherProcessPorts:
            connections.append(rpyc.connect("localhost",port))


    def exposed_requestCriticalSection(self,otherTimestamp,processID):
        mutex.acquire()
        global TIMESTAMP
        global messageTracker
        returnValue=None
        print(f"RECEIVER: {thisPort}\t, SENDER_TM: {otherTimestamp}\t, RECEIVER_TM: {TIMESTAMP}\t,SENDER:{processID}\t receiverState: {thread.state}")
        if(thread.state==DONOTWANT):
            t=max(TIMESTAMP,otherTimestamp)+1
            TIMESTAMP=t
            returnValue="OK"
        elif(thread.state=="wanting" or thread.state=="want"):
            if(otherTimestamp<TIMESTAMP):
                returnValue="OK"
            else:
                messageTracker.append(processID)
        elif(thread.state==HELD):
            messageTracker.append(processID)
        mutex.release()
        return returnValue




    def exposed_ack(self,processID):
        print(f"ACK: OK from {processID} to {thisPort}")
        mutex.acquire()
        global okCount
        global TIMESTAMP
        TIMESTAMP+=1
        okCount+=1
        mutex.release()
    
    def exposed_list(self):
        # utility method to list proceeses
        mutex.acquire()
        returnValue=thread.state
        if(thread.state=="wanting" or thread.state=="want"):
            returnValue = WANTED
        mutex.release()
        return returnValue


     

 
if __name__=='__main__':
 t=ThreadedServer(ProcessService, port=thisPort)
 t.start()