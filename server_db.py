__author__ = 'len'

import asyncio
import websockets
import json
import time
import datetime
import pymysql

class server:
    def __init__(self):
        self.mode = input("Input the mode(winter/summer):")
        self.running_num = int(input("Input the max running number:"))

        self.info = {}
        self.key = 1
        self.now_running_num = 0
        if self.mode == "winter":
            self.temp_max = 30
            self.temp_min = 25
        elif self.mode == "summer":
            self.temp_max = 25
            self.temp_min = 18

    def record(self,cid,temp,speed,target,state,cost):
        self.info[cid] = [temp,speed,target,state,cost]

    def calculate_time(self,cid):#maybe useful or useless
        past_time = datetime.datetime.strptime(self.info[cid][5],'%Y-%m-%d %H:%M:%S')
        return (datetime.datetime.now()-past_time).seconds

    def calculate_now_temperature(self,cid):
        if self.info[cid][3] == "running":
            if self.mode == "winter":
                if self.info[cid][1] == "high":
                    now_temperature = self.info[cid][0] + self.calculate_time(cid)/10
                elif self.info[cid][1] == "medium":
                    now_temperature = self.info[cid][0] + self.calculate_time(cid)/15
                elif self.info[cid][1] == "low":
                    now_temperature = self.info[cid][0] + self.calculate_time(cid)/20
            elif self.mode == "summer":
                if self.info[cid][1] == "high":
                    now_temperature = self.info[cid][0] - self.calculate_time(cid)/10
                elif self.info[cid][1] == "medium":
                    now_temperature = self.info[cid][0] - self.calculate_time(cid)/15
                elif self.info[cid][1] == "low":
                    now_temperature = self.info[cid][0] - self.calculate_time(cid)/20
        else:
            now_temperature = self.info[cid][0]
        self.info[cid][0] = now_temperature
        return int(now_temperature)

    def calculate_cost(self,cid):
        if self.info[cid][3] == "running":
            timezone = (datetime.datetime.now()-datetime.datetime.strptime(self.info[cid][5],'%Y-%m-%d %H:%M:%S')).seconds
            if self.info[cid][1] == "high":
                cost = self.info[cid][4] + timezone/10
            elif self.info[cid][1] == "medium":
                cost = self.info[cid][4] + timezone/12
            elif self.info[cid][1] == "low":
                cost = self.info[cid][4] + timezone/15
        else:
            cost = self.info[cid][4]
        self.info[cid][4] = cost
        self.info[cid][5] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
        return round(cost,2)

    def dispatch(self):
        pass

    def get_record_fromdatabase(self):
        pass
    def send_to_database(self,str1):
        if str1['method'] =="handshake":
            time_str = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            database_exec = "insert into running_status (room_id,optime,optype,req_temp_start,req_temp_end,speed)values('" +str(str1['cid'])+"','"+str(time_str)+"','on','"+str(str1['temp'])+"','"+str(str1['target'])+"','"+str1['speed']+"');"
            print(database_exec)
            sta=cur.execute(database_exec)
        elif str1['method'] =="set":
            time_str = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            database_exec = "insert into running_status (room_id,optime,optype,req_temp_end,speed)values('"+str(str1['cid'])+"','"+str(time_str)+"','set','"+str(str1['target'])+"','"+str1['speed']+"');"
            print(database_exec)
            sta=cur.execute(database_exec)
        elif str1['method'] =="get":
            pass
        elif str1['method'] =="changed":
            time_str = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            database_exec = "insert into running_status (room_id,optime,optype,req_temp_start)values('"+str(str1['cid'])+"','"+str(time_str)+"','changed','"+str(str1['temp'])+"');"
            print(database_exec)
            sta=cur.execute(database_exec)
        elif str1['method'] =="shutdown":
            time_str = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            database_exec = "insert into running_status (room_id,optime,optype)values('"+str(str1['cid'])+"','"+str(time_str)+"','off');"
            print(database_exec)
            sta=cur.execute(database_exec)
        elif str1['method'] == "report":
           #database_exec = "select * from running_status where (room_id ="+str1['cid'] +");"
           #print(database_exec)
           #cur.execute(database_exec)
           #for each in cur:
           #    print(each)
           pass
        elif str1['method'] == "checkout":
            pass
        conn.commit()
    def judge(self,str1):
        if str1['method'] =="handshake":
            self.record(str1['cid'],int(str1['temp']),str1['speed'],int(str1['target']),"running",0)
            dealed = {"method":"handshake","result":"ok","config":{"mode":self.mode,"temp-max":self.temp_max,"temp-min":self.temp_min},"state":"running"}
            time_str = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            self.info[str1['cid']] = self.info[str1['cid']] + [time_str]
            self.key = 1
            self.now_running_num += 1
            self.info[str1['cid']][3] = "running"
        elif str1['method'] =="set":
            self.dispatch()
            if self.mode == "winter":
                if int(str1['target']) > self.info[str1['cid']][0]:
                    self.info[str1['cid']][1] = str1['speed']
                    self.info[str1['cid']][2] = int(str1['target'])
                    state = "running"
                    self.key = 1
                    if self.info[str1['cid']][3] != "running":
                        self.now_running_num += 1
                        self.info[str1['cid']][3] = "running"
                        self.info[str1['cid']][5] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
                else:
                    self.info[str1['cid']][1] = str1['speed']
                    self.info[str1['cid']][2] = int(str1['target'])
                    state = "standby"
                    if self.info[str1['cid']][3] != "standby":
                        self.now_running_num -= 1
                        self.key = 0
                        self.info[str1['cid']][3] = "standby"
                        self.info[str1['cid']][0] = self.calculate_now_temperature(str1['cid'])
                        self.info[str1['cid']][4] = self.calculate_cost(str1['cid'])
                        self.info[str1['cid']][5] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            else:
                if int(str1['target']) < self.info[str1['cid']][0]:
                    self.info[str1['cid']][1] = str1['speed']
                    self.info[str1['cid']][2] = int(str1['target'])
                    state = "running"
                    self.key = 1
                    if self.info[str1['cid']][3] != "running":
                        self.now_running_num += 1
                        self.info[str1['cid']][3] = "running"
                        self.info[str1['cid']][5] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
                else:
                    self.info[str1['cid']][1] = str1['speed']
                    self.info[str1['cid']][2] = int(str1['target'])
                    state = "standby"
                    if self.info[str1['cid']][3] != "standby":
                        self.now_running_num -= 1
                        self.key = 0
                        self.info[str1['cid']][3] = "standby"
                        self.info[str1['cid']][0] = self.calculate_now_temperature(str1['cid'])
                        self.info[str1['cid']][4] = self.calculate_cost(str1['cid'])
                        self.info[str1['cid']][5] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            dealed = {"method":"set","state":state}
        elif str1['method'] =="get":
            temp = self.calculate_now_temperature(str1['cid'])
            if self.mode == "winter":
                if temp >= self.info[str1['cid']][2]:
                    cost = self.calculate_cost(str1['cid'])
                    self.info[str1['cid']][3] = "standby"
                    state = "standby"
                    self.now_running_num -= 1
                else:
                    state = "running"
            else:
                if temp <= self.info[str1['cid']][2]:
                    self.info[str1['cid']][3] = "standby"
                    state = "standby"
                    self.now_running_num -= 1
                else:
                    state = "running"
            cost = self.calculate_cost(str1['cid'])
            dealed = {"method":"get","temp":temp,"state":state,"cost":cost}
        elif str1['method'] =="changed":
            if self.mode == "winter":
                if (int(str1['temp'])+2) >= self.info[str1['cid']][2]:
                    self.info[str1['cid']][0] = int(str1['temp'])
                    state = "standby"
                else:
                    self.info[str1['cid']][0] = int(str1['temp'])
                    self.info[str1['cid']][3] = "running"
                    self.now_running_num += 1
                    state = "running"
                    self.key = 1
                    self.info[str1['cid']][5] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            else:
                if (int(str1['temp'])-2) <= self.info[str1['cid']][2]:
                    self.info[str1['cid']][0] = int(str1['temp'])
                    state = "standby"
                else:
                    self.info[str1['cid']][0] = int(str1['temp'])
                    self.key = 1
                    self.info[str1['cid']][3] = "running"
                    self.now_running_num += 1
                    state = "running"
                    self.info[str1['cid']][5] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            dealed = {"method":"changed","state":state}
        elif str1['method'] =="shutdown":
            if self.info[str1['cid']] == "running":
                self.now_running_num -= 1
                self.key = 0
                self.info[str1['cid']][3] = "shutdown"
                self.info[str1['cid']][0] = self.calculate_now_temperature(str1['cid'])
                self.info[str1['cid']][4] = self.calculate_cost(str1['cid'])
                self.info[str1['cid']][5] = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
            else:
                self.info[str1['cid']][3] = "shutdown"
            dealed = {"method":"shutdown","result":"ok","state":"shutdown"}
        elif str1['method'] == "report":
            database_exec = "select * from running_status where (room_id ="+str1['cid'] +");"
            print(database_exec)
            cur.execute(database_exec)
            dealed = {"method":"report","state":123}
        elif str1['method'] == "checkout":
            dealed = {"method":"report"}
        return dealed

    @asyncio.coroutine
    def hello(self,websocket, path):
        var = 1
        if self.now_running_num < self.running_num:
            while var==1:
                decodejson = yield from websocket.recv()
                rec = json.loads(decodejson)
                print(rec)
                dealed_str = self.judge(rec)
                self.send_to_database(rec)
                print(dealed_str)
                encodejson = json.dumps(dealed_str)
                yield from websocket.send(encodejson)


s1 = server()
start_server = websockets.serve(s1.hello, 'localhost', 6666)
sql_name = input("Input the name of database:")
sql_username = input("Input the username of database")
sql_password = input("Input the password of database:")
conn=pymysql.connect(host='localhost',user=sql_username,passwd=sql_password,db=sql_name,charset='utf8')
cur=conn.cursor()
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

