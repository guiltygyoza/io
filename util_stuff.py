import yaml
import random
from datetime import datetime, date
from util_people import *
import arrow

class StuffDB:
    def __init__(self, yaml_file_stuff, yaml_file_people):
        self.yaml_file_stuff = yaml_file_stuff
        self.yaml_file_people = yaml_file_people
        self.sections = ['appointment', 'today', 'growth', 'done', 'deleted']
        with open(yaml_file_stuff) as file:
            self.db = yaml.load(file, Loader=yaml.FullLoader) # FullLoader converts yaml scalar values to Python dictionaries
        with open(yaml_file_people) as file:
            self.people = yaml.load(file, Loader=yaml.FullLoader) 

    def nxt(self, avail):
        if len(self.db["today"]) == 0:
            print("You have no work left for today! Please proceed to growth.")
            return

        l = []
        for each in self.db["today"]:
            if int(each["time"]) <= avail:
                l.append(each)
        if len(l)>0:
            chosen = random.choice(l)
            print(f"Please complete {bcolors.GREEN}{chosen['name']}{bcolors.ENDC} in {bcolors.GREEN}{chosen['time']}{bcolors.ENDC} minutes.")
        else:
            t=10000
            for each in self.db["today"]:
                if int(each["time"]) <= t:
                    t = int(each["time"])
                    chosen = each
            print(f"No task is completable within your {avail} minutes. The closest option is:")
            print(f"> Please complete {bcolors.GREEN}{chosen['name']}{bcolors.ENDC} in {bcolors.GREEN}{chosen['time']}{bcolors.ENDC} minutes.")


    def add(self, typ, name, time):
        new_task = {'index':'x', 'name':name, 'time':time}
        if typ == 'a':
            self.db["appointment"].append(new_task)
        elif typ == 't':
            self.db["today"].append(new_task)
        elif typ == 'g':
            self.db["growth"].append(new_task)
        self.update()

    def done(self, idx_s):
        for idx in idx_s:
            if idx[0] == 'a':
                self._move("done", idx, "appointment")
            elif idx[0] == 't':
                self._move("done", idx, "today")
            elif idx[0] == 'g':
                self._move("done", idx, "growth")
        self.update()
    
    def _move(self, dest, idx, section):
        j = None
        for i in range(len(self.db[section])):
            if self.db[section][i]['index'] == idx:
                j = i
                break
        if j is None:
            print("> No such task index.")
        else:
            self.db[dest].append(self.db[section][j])
            del self.db[section][j]

    def print_la(self):
        for section in self.sections:
            if (section != 'done') and (section != 'deleted'):
                self.printTable(section)
        print()
    
    def print_laa(self):
        for section in self.sections:
            self.printTable(section)
        print()
    
    def print_(self, section):
        printTable(section)
        print()

    def print(self):
        print()
        print(self.db)

    def printTable(self, section):
        """ 
        Description: Pretty print a list of dictionaries (myDict) as a dynamically sized table.
        Author: Thierry Husson - Use it as you want but don't blame me.
        Link: https://stackoverflow.com/questions/17330139/python-printing-a-dictionary-as-a-horizontal-table-with-headers
        """
        print()
        print(f"{bcolors.GREEN}{bcolors.UNDERLINE}{section}{bcolors.ENDC}")
       
        if len(self.db[section]) == 0: return

        colList = ['index', 'name', 'time']
        myDict = self.db[section]
        #myList = [colList] # 1st row = header
        myList = []
        for item in myDict: myList.append([str(item[col] if item[col] is not None else '') for col in colList])
        colSize = [max(map(len,col)) for col in zip(*myList)]
        formatStr = ' | '.join(["{{:<{}}}".format(i) for i in colSize])
        #myList.insert(0, ['-' * i for i in colSize]) # Seperating line
        for item in myList: print(formatStr.format(*item))
    
    def update(self):
        ## update db
        for section in self.sections:
            for i, each in enumerate(self.db[section]):
                each['index'] = f"{section[0]}{i+1}"
        
        ## update yaml
        with open(self.yaml_file_stuff, 'w') as file:
                documents = yaml.dump(self.db, file)
        with open(self.yaml_file_people, 'w') as file:
                documents = yaml.dump(self.people, file)

    def sync_people(self):
        today = arrow.get(date.today())
        names = []
        names_type = []
        for name in self.people:
            p = self.people[name]
            ## first check for events; assume events are always annually-recurring
            if len(p["events"])>0:
                for event in p["events"]: # event = {'name':name_of_event, 'date':date_of_event}
                    d = arrow.get(event["date"])
                    if (d.day == today.day) and (d.month == today.month) and (p["ping_last"] != str(date.today())):
                        names.append(name)
                        names_type.append(event["name"])
            ## then check for regular pinging
            else:
                diff = today - arrow.get(p["ping_last"])
                diff = diff.days
                if diff >= p["ping_freq"]:
                    names.append(name)
                    names_type.append('regular')

        if len(names) > 0:
            names_colored = [f"{bcolors.PINK}{n}{bcolors.ENDC}" for n in names]
            names_colored = ", ".join(names_colored)
            print()
            print(f"> Today is the day to ping: {names_colored}")

            ## generate appointments to stuff; each ping takes 10 minutes
            for name, typ in zip(names, names_type):
                self.add('a', f'Ping {name} ({typ})', 10)

            ## change ping_last to today, assuming the ping will always be carried out
            for name, typ in zip(names, names_type):
                p = self.people[name]
                p["ping_last"] = str(date.today())
                self.people[name] = p
        
            ## update databases
            self.update()
        
    def lp(self):
        names = [n for n in self.people]
        print(", ".join(names))


    def addp(self, name, freq, last):
        p = {
                "ping_freq" : freq,
                "ping_last" : last,
                "note" : "",
                "events" : []
            }
        self.people[name] = p
        self.update()