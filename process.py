"""In this version of the server main replica resets when another client connects """
from multiprocessing import connection
import rpyc
from rpyc.utils.server import ThreadedServer
import datetime
date_time=datetime.datetime.now()


import time
from functools import wraps
import sys
import datetime
import _thread
import time
import random

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
    def changeStateAcvtive(self):
        self.state=HELD
    def changeStatePassive(self):
        self.state=DONOTWANT
    def changeStateWant(self):
        self.state="want"

    def stop(self):
        _thread.exit()
    def set_Data(self,newData):
        self.setData=newData
    def run(self):
        # updating data with cache time
        global okCount
        global messageTracker
        global otherProcessPorts
        while True:
            if self.state==DONOTWANT:
                randomWait=random.randrange(5,15)
                # randomWait=self.passiveTime

                # if(self.passiveTime!=5):
                #     randomWait=random.randrange(5,self.passiveTime)

                time.sleep(randomWait)
                self.state="wanting"

            elif(self.state==HELD):
                # randomWait=self.criticalSectionTime
                randomWait=random.randrange(10,15)
                # if(self.criticalSectionTime!=10):
                #     randomWait=random.randrange(10,self.criticalSectionTime)

                time.sleep(randomWait)
                print(f"MessageTracer: {messageTracker} thisport: {thisPort}, type: {type(otherProcessPorts)}")
                for port in messageTracker:
                    index=otherProcessPorts.index(port)
                    conn=connections[index]
                    conn.root.ack(thisPort)

                messageTracker=[]
                okCount=0
                self.changeStatePassive()
            elif(self.state=="wanting"):
                global TIMESTAMP
                currentTimestamp=TIMESTAMP

                for conn in connections:
                    res=conn.root.requestCriticalSection(currentTimestamp,thisPort)
                    print(res)
                    if(res=="OK"):
                        okCount+=1

                self.state="want"
                if(okCount==len(otherProcessPorts)):
                    self.changeStateAcvtive()
            elif(self.state=="want"):
                if(okCount>=len(otherProcessPorts)):
                    self.changeStateAcvtive()





def tick(running,dummy):
    while running:
        pass



def cache(replicas:list,time):
    for p in replicas:
        p.cacheTime=time
    print(f"Cache time for update: {time}")








def update(mainReplica,replicas,newData):
    mainReplica.data=newData
    for r in replicas:
        r.set_Data(mainReplica.data)


thread=Process()
thread.start()
connections=[]


# start a separate thread for system tick
_thread.start_new_thread(tick, (running,"skdj"))

class ProcessService(rpyc.Service):
    def exposed_other_ps_ports(self,ports):
        global otherProcessPorts
        global connections
        for port in ports:
            otherProcessPorts.append(port)
        for port in otherProcessPorts:

            connections.append(rpyc.connect("localhost",port))
    def exposed_exit(self):

        try:
            t.close()
        except:
            pass


    def exposed_requestCriticalSection(self,otherTimestamp,processID):
        global TIMESTAMP
        global messageTracker

        print(f"RECEIVER: {thisPort}\t, SENDER_TM: {otherTimestamp}\t, RECEIVER_TM: {TIMESTAMP}\t,SENDER:{processID}\t receiverState: {thread.state}")
        if(thread.state==DONOTWANT):
            t=max(TIMESTAMP,otherTimestamp)+1
            TIMESTAMP=t
            return "OK"
        elif(thread.state=="wanting" or thread.state=="want"):
            if(otherTimestamp<TIMESTAMP):
                return "OK"
            else:
                messageTracker.append(processID)
        elif(thread.state==HELD):
            messageTracker.append(processID)




    def exposed_ack(self,processID):
        print(f"ACK: OK from {processID} to {thisPort}")
        global okCount
        okCount+=1
    def exposed_list(self):
        # utility method to list proceeses
        if(thread.state=="wanting" or thread.state=="want"):
            return WANTED
        return thread.state

    def exposed_command(self,command):
        print(f"Received command from client: {command}")
        cmd = command.split(" ")

        command = cmd[0]

        if len(cmd) > 3:
            print("Too many arguments")

        # handle exit
        elif command == "exit":
            running=False
            self.replicas=[]
            print("Program exited")
            return False

        # handle list
        elif command == "list":
            try:
                self.list()
            except:
                print("Error")

        # handle clock
        # elif command == "update":
        #     try:
        #         update(mainReplica,self.replicas,cmd[1])
        #     except:
        #         print("Error")
        # handle kill <ID>
        elif command == "cache":
            try:
                id = int(cmd[1])
                cache(self.replicas,id)
            except:
                print("Error")


        # handle unsupported command        
        else:
            print("Unsupported command:", cmd)

     

 
if __name__=='__main__':
 t=ThreadedServer(ProcessService, port=thisPort)
 t.start()