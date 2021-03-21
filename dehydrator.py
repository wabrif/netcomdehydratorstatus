#!/usr/bin/env python2

"""Retrieve and log the status of Netcomm dehydrators 
version='1.0.2'
'Programming Language :: Python :: 2'
"""

from __future__ import print_function
import ConfigParser
#import requests -> Code fails in python3 because http.client gives BadStatusLine to the response from the dehydrator, re-written to use older version of httplib in python2
import httplib
import datetime
import argparse
import subprocess
import os

def load_config(conf_file):
    '''
    Read an ini file containing station parameters
    
    filename: string, containing path and filename
        
    returns: ConfigParser instance, parser
    '''
    config = ConfigParser.ConfigParser()
    config.readfp(open(conf_file))
    return config
    
def getstatus(siteURI):
    '''
    Gets status of the dehydrator

    siteURI: string, containing the URI of the site

    returns: string, status message
    '''
    #Code using httplib
    fullURI = siteURI
    try:
        conn = httplib.HTTPConnection(fullURI)
        headers = {'Content-type': 'text/plain;charset=UTF-8', 'Accept':'text/plain'}
        conn.request('POST', '/status.cgi', 'S', headers)
        r = conn.getresponse()
        status = r.read()
        #print(status)
    except:
        status =  "?;?;?;?;?;?;?;"
        #raise
    return status
    
def getconfig(siteURI):
    '''
    Gets config of the dehydrator

    siteURI: string, containing the URI of the site

    returns: string, config message
    '''
    fullURI = siteURI
    #configlist = ['VA','VR','IC','PL','IX','SX','CX','MX','RX','RM']
    try:
        config = {'VA':'','VR':'','IC':'','PL':'','IX':'','SX':'','CX':'','MX':'','RX':'','RM':''}
        for item in config:
            conn = httplib.HTTPConnection(fullURI)
            headers = {'Content-type': 'text/plain;charset=UTF-8', 'Accept':'text/plain'}
            conn.request('POST', '/config.cgi', item, headers)
            r = conn.getresponse()
            config[item] = r.read()
    except:
        config =  {}
    return config
 
def statemasterslave(state):
    '''
    Gets the state of the dehydrator and returns the masterslave state
    
    state: string, state message
    
    returns: string, state of master slave
    '''
    try:
        if state[0] == 'S':
            masterslave="Slave"
        elif state[0] == 'M':
            masterslave="Master"
        elif state[0] == 'N':
            masterslave="Master Offline"
        elif state[0] == 'P':
            masterslave="Parallel Master"
        elif state[0] == 'Q':
            masterslave="Parallel Master Offline"
        else:
            masterslave="???"
    except:
        masterslave="???"
    return masterslave
    
def statesuperstate(state):
    '''
    Gets the state of the dehydrator and returns the superstate state
    
    state: string, state message
    
    returns: string, superstate
    '''
    try:
        if state[1] == 'N':
            superstate="Normal"
        elif state[1] == 'S':
            superstate="Standby"
        elif state[1] == 'L':
            superstate="Leaky"
        elif state[1] == 'R':
            superstate="Remote"
        elif state[1] == 'J':
            superstate="PM: joint pumping"
        elif state[1] == 'U':
            superstate="PM: slave pumping"
        elif state[1] == 'I':
            superstate="PM: solo pumping"        
        else:
            superstate="???"
    except:
        superstate="???"
    return superstate

def stateenv(state):    
    '''
    Gets the state of the dehydrator and returns the environment state
    
    state: string, state message
    
    returns: string, environment state
    '''
    try:
        if state[2] == 'N':
            env="Normal"
        elif state[2] == 'C':
            env="Cold"
        elif state[2] == 'H':
            env="Hot"
        else:
            env="???"
    except:
        env="???"
    return env

def statecan1cnt(state):
    '''
    Gets the state of the dehydrator and returns the can1 condition
    
    state: string, state message
    
    returns: string, can1 condition
    '''
    try:
        if state[3] == 'O':
            can1cnt="Ready"
        elif state[3] == 'F':
            can1cnt="Full"
        elif state[3] == 'U':
            can1cnt="Init."
        elif state[3] == 'D':
            can1cnt="Dead"    
        else:
            can1cnt="???"
    except:
        can1cnt="???"
    return can1cnt

def statecan1use(state):
    '''
    Gets the state of the dehydrator and returns the can1 use condition
    
    state: string, state message
    
    returns: string, can1 use condition
    '''
    try:
        if state[4] == 'I':
            can1use="Idle"
        elif state[4] == 'U':
            can1use="In use"
        elif state[4] == 'R':
            can1use="Regenerating"
        else:
            can1use="???"
    except:
        can1use="???"
    return can1use

def statecan2cnt(state):
    '''
    Gets the state of the dehydrator and returns the can2 condition
    
    state: string, state message
    
    returns: string, can2 condition
    '''
    try:
        if state[5] == 'O':
            can2cnt="Ready"
        elif state[5] == 'F':
            can2cnt="Full"
        elif state[5] == 'U':
            can2cnt="Init."
        elif state[5] == 'D':
            can2cnt="Dead"    
        else:
            can2cnt="???"
    except:
        can2cnt="???"
    return can2cnt

def statecan2use(state):
    '''
    Gets the state of the dehydrator and returns the can2 use condition
    
    state: string, state message
    
    returns: string, can2 use condition
    '''
    try:
        if state[6] == 'I':
            can2use="Idle"
        elif state[6] == 'U':
            can2use="In use"
        elif state[6] == 'R':
            can2use="Regenerating"
        else:
            can2use="???"
    except:
        can2use="???"
    return can2use
    
def alarms(alarm):
    '''
    Gets the state of the alarms and returns a description of current alarms
    
    state: string, alarm message
    
    returns: list, alarms
    '''
    #Needs testing
    alarmdef =  "1:  low pressure", "2:  high pressure", "3:  leaky (high duty cycle)", "4:  too hot", "5:  too cold", "6:  low voltage (system error)", "7:  canister 1 won't heat", "8:  canister 1 won't cool", "9:  canister 2 won't heat", "10: canister 2 won't cool", "11: very leaky (shut down)", "12: dew point alarm", "13: compressor timeout (system error)", "14: comm error", "15: canister 1 thermistor bad", "16: canister 2 thermistor bad", "17: ambient thermistor bad", "18: overpressure", "19: calibration factors corrupted", "20: pressure limits corrupted", "21: short duty cycle", "22: abandoned pumping"
    alarmlist = []
    for i, c in enumerate(alarm):
        if c != '-' and c != '?':
            alarmlist.append(alarmdef[i])
    return alarmlist
    
def tempC(tempF):
    '''
    Gets the temp in F and returns in C
    
    temp: string, temp F
    
    returns: string, temp C
    '''
    temp = grabnumber(tempF)
    try:
        tempC = (float(temp) - 32) / 1.8
        tempC = str(round(tempC, 1))
    except:
        tempC = '?'
    return tempC

def grabnumber(vstring):
    '''
    Grabs out the number out of parameter string
    
    vstring: string, the string to process
    
    returns: string, just the numerical part
    '''
    # Courtesy of LGC
    validchar = ('0','1','2','3','4','5','6','7','8','9','.','-','+')
    number = []
    for char in vstring:
        if char in validchar:
            number.append(char)
    number = ''.join(number)
    return number
    
def loadallstations(stn_config):
    '''
    Loads the status message from all stations    
    
    stn_config: ConfigParser instance,  contains the station configs
    
    returns: dict, a dictionary containing the status of the sites
    '''
    stn_config
    statusdict = {}
    for site in stn_config.sections():
        if stn_config.has_option(site,'dehydrator') and stn_config.get(site,'dehydrator') != "None":
            sitename = stn_config.get(site,'sitename')
            siteURI = stn_config.get(site,'dehydrator')
            status = getstatus(siteURI)
            statusdatetime = datetime.datetime.now().strftime('%Y%m%d %H%M')
            pressure,ontime,tottime,state,temp,alarm,hours,empty = status.split(";")
            pressure = grabnumber(pressure)
            try:
                dutycycle = 100 * float(ontime) / float(tottime)
                dutycycle = str(round(dutycycle, 2))
            except:
                dutycycle = '?'
            statusdict[site] = {'sitename': sitename, 'statusdatetime': statusdatetime, 'pressure': pressure, 'dutycycle': dutycycle, 'ontime': ontime, 'tottime': tottime, 'state': state, 'temp': temp, 'alarm': alarm, 'hours': hours}
    return statusdict
    
def displaystations(statusdict):
    '''
    Displays the status message from all stations    
    
    statusdict: dict, a dictionary containing the status of the sites
    
    returns: 
    '''
    for site in statusdict:
        print()
        print(statusdict[site]['sitename'])
        print(statusdict[site]['alarm'])
        alarmlist = alarms(statusdict[site]['alarm'])
        if len(alarmlist):
            print(alarms(statusdict[site]['alarm']))
        else:
            print('No alarms')
        print('Pressure: ',statusdict[site]['pressure'])
        print('Duty Cycle: ',statusdict[site]['dutycycle'],'%')
        print('Pumping ',statusdict[site]['ontime'],' out of ',statusdict[site]['tottime'],' seconds')
        print('Temperature: ',statusdict[site]['temp'],' (',tempC(statusdict[site]['temp']),')')
        print('Compressor Hours: ',statusdict[site]['hours'])
        print('State: ',statusdict[site]['state'])
        print('Control: ',statemasterslave(statusdict[site]['state']))
        print('Status: ',statesuperstate(statusdict[site]['state']))
    return
    
def createlogfiles(base_path, stn_config, statusdict):
    '''
    Writes the dehydrator logs
    
    base_path: string, the base path to create the full path from
    stn_config: ConfigParser instance,  contains the station configs
    statusdict: dict, a dictionary containing the status of the sites
    
    returns:
    '''
    dehydratorlogdir = 'dehydrator/'
    filename = 'dehydrator.log'
    for site in statusdict:
        path_file = base_path + stn_config.get(site,'path') + dehydratorlogdir + filename
        try:
            with open(path_file, 'a') as file:
                #if statusdict[site]['pressure'] != '?' and statusdict[site]['dutycycle'] != '?': <-not required with gnuplot
                log = statusdict[site]['statusdatetime'] + ' ' + statusdict[site]['pressure'] + ' ' + statusdict[site]['dutycycle'] + ' ' + tempC(statusdict[site]['temp']) + '\n'
                file.write(log)
        except:
            print('Failed to open ',path_file)
    return

def creategraphs(base_path, stn_config, statusdict):
    '''
    Writes the dehydrator graphs
    
    base_path: string, the base path to create the full path from
    stn_config: ConfigParser instance,  contains the station configs
    statusdict: dict, a dictionary containing the status of the sites
    
    returns:
    '''

    dehydratorlogdir = 'dehydrator/'
    filename = 'dehydrator.log'
    for site in statusdict:
        pathnfilein = base_path + stn_config.get(site,'path') + dehydratorlogdir + filename  
        datem7 = datetime.datetime.now() - datetime.timedelta(days=6)
        datem30 = datetime.datetime.now() - datetime.timedelta(days=29)
        # Graph from current time
        #mintime7 = datem7.strftime('%Y%m%d%H%M')
        #maxtime7 = datetime.datetime.now().strftime('%Y%m%d%H%M')
        #mintime30 = datem30.strftime('%Y%m%d%H%M')
        #maxtime30 = datetime.datetime.now().strftime('%Y%m%d%H%M')
        # Graph from midnight to midnight
        mintime7 = datem7.strftime('%Y%m%d') + "0000"
        maxtime7 = datetime.datetime.now().strftime('%Y%m%d') + "2359"
        mintime30 = datem30.strftime('%Y%m%d') + "0000"
        maxtime30 = datetime.datetime.now().strftime('%Y%m%d') + "2359"

        #Start of png 7 day generation
        try:
            pathnfileout7 = open(base_path + stn_config.get(site,'path') + dehydratorlogdir + '7day.png', 'w')
            proc = subprocess.Popen(['/usr/bin/gnuplot'], 
                        shell=True,
                        stdin=subprocess.PIPE,
                        stdout=pathnfileout7,
                        )
          
            proc.stdin.write("set term png\n") #for newer version of GNUplot
            proc.stdin.write("set title 'Graph of dehydrator pressure and duty cycle for 7 days '\n")
            proc.stdin.write("set style data linespoints\n")
            proc.stdin.write("set size 1.0,1.0\n")
            proc.stdin.write("set ytics nomirror\n")
            proc.stdin.write("set y2tics 1, 1\n")
            proc.stdin.write("set ylabel 'Pressure (psi)'\n")
            proc.stdin.write("set y2label 'Duty cycle (%)'\n")
            proc.stdin.write("set yrange [ 1:4 ]\n")
            proc.stdin.write("set y2range [ 0:10 ]\n")
            proc.stdin.write('set timefmt "%Y%m%d %H%M"\n')
            proc.stdin.write("set xdata time\n")
            proc.stdin.write("set xlabel 'Time'\n")
            proc.stdin.write('set format x "%d/%m\\n%H:%M"\n')
            proc.stdin.write("set grid\n")
            proc.stdin.write("set key left\n")
            line = 'set xrange ["' + mintime7 + '":"' + maxtime7 + '" ]\n'
            proc.stdin.write(line)
            line = 'plot "' + pathnfilein + '"' + "  using 1:3 axes x1y1 t \'Pressure\' , " + '"' + pathnfilein + '"' + "  using 1:4 axes x1y2 t \'Duty cycle\' \n"
            proc.stdin.write(line)
            proc.stdin.close()
            proc.wait()
            pathnfileout7.close()
        except:
            print('Failed to create 7 day graphs')
        
        #Start of png 30 day generation
        try:
            pathnfileout30 = open(base_path + stn_config.get(site,'path') + dehydratorlogdir + '30day.png', 'w')
            proc = subprocess.Popen(['/usr/bin/gnuplot'], 
                        shell=True,
                        stdin=subprocess.PIPE,
                        stdout = pathnfileout30,
                        )
                        
            proc.stdin.write("set term png\n") #for newer version of GNUplot
            proc.stdin.write("set title 'Graph of dehydrator pressure and duty cycle for 30 days '\n")
            proc.stdin.write("set style data lines\n")
            proc.stdin.write("set size 1.0,1.0\n")
            proc.stdin.write("set ytics nomirror\n")
            proc.stdin.write("set y2tics 1, 1\n")
            proc.stdin.write("set ylabel 'Pressure (psi)'\n")
            proc.stdin.write("set y2label 'Duty cycle (%)'\n")
            proc.stdin.write("set yrange [ 1:4 ]\n")
            proc.stdin.write("set y2range [ 0:10 ]\n")
            proc.stdin.write('set timefmt "%Y%m%d %H%M"\n')
            proc.stdin.write("set xdata time\n")
            proc.stdin.write("set xlabel 'Time'\n")
            proc.stdin.write('set format x "%d/%m\\n%H:%M"\n')
            proc.stdin.write("set grid\n")
            proc.stdin.write("set key left\n")
            #Uncomment the next two lines once the logs reach 30 days
            line = 'set xrange ["' + mintime30 + '":"' + maxtime30 + '" ]\n'
            proc.stdin.write(line)
            line = 'plot "' + pathnfilein + '"' + "  using 1:3 axes x1y1 t \'Pressure\' , " + '"' + pathnfilein + '"' + "  using 1:4 axes x1y2 t \'Duty cycle\' \n"
            proc.stdin.write(line)
            proc.stdin.close()
            proc.wait()
            pathnfileout30.close()
        except:
            print('Failed to create 30 day graphs')
    return
 
def main():
    base_path = '/var/log/www'
    conf_file = '/home/python/webpageframework/stations.ini'
  
    parser = argparse.ArgumentParser(description='Dehydrator monitoring')
    parser.add_argument("-d", "--display", action="store_true",
                  help="Display dehydrator status")
    parser.add_argument("-l", "--log", action="store_true",
                  help="Log the dehydrator pressure/duty cycle")

    args = parser.parse_args()    
    if args.display:
        stn_config = load_config(conf_file)
        statusdict = loadallstations(stn_config)
        displaystations(statusdict)
    elif args.log:
        stn_config = load_config(conf_file)
        statusdict = loadallstations(stn_config)
        createlogfiles(base_path, stn_config, statusdict)
        creategraphs(base_path, stn_config, statusdict)
    else:
        print('Use --help to see the available options')
  
if __name__ == "__main__":
    main()
