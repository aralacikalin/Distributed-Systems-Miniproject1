from urllib import response
import rpyc
import sys
 
if len(sys.argv) < 2:
   exit("Usage {} SERVER".format(sys.argv[0]))
 
server = sys.argv[1]

conn = rpyc.connect(server,15200)
running = True

while running:
        inp = input("Input the command: ").lower()
        response=conn.root.command(inp)
        if(response!=None):
           running=response





 
 