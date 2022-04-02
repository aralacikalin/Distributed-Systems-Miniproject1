
import sys
import subprocess
import rpyc
import time 

number_of_processes = int(sys.argv[1])

print(f'N={number_of_processes}')

start_port = 15229

processes_port = []
processes = []
for i in range(number_of_processes):
    processes_port.append( start_port+i )
    port_as_string = str(start_port+i)
    cmd = 'python process.py ' + port_as_string
    print( 'cmd', cmd.split() )
    p = subprocess.Popen( cmd.split() )
    processes.append(p)

def all_ports_except( all_ports, port_to_exclude ):
    output = []
    for port in all_ports:
        if port == port_to_exclude:
            continue
        output.append( port )
        
    return output

time.sleep(2)

connections = []
for port in processes_port:
    connections.append( rpyc.connect('localhost',port) )

for idx, conn in enumerate(connections):
    other_ps_ports = all_ports_except( processes_port, processes_port[idx] )
    conn.root.other_ps_ports( other_ps_ports )
running=True
while running:
    print( "Input the command: " )
    command = input()
    for idx, conn in enumerate(connections):
        if command.lower() == 'list':
            process_output = conn.root.list()
            print( f'P{idx} out={process_output}' )
        elif command.lower() == 'exit':
            try:
                running=False
                conn.root.exit()
            except:
                break
            break
        else:
            cmd_name, value = command.split()

            if cmd_name.lower() == 'time-cs':
                conn.root.time_cs( int(value) )
            elif cmd_name.lower() == 'time-p':
                conn.root.time_p( int(value) )

# TODO: wait for all process to finish


for conn in connections:
   conn.root.exit()
