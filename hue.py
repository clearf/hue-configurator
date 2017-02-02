import json
import requests
import re
import pprint
import house

pp = pprint.PrettyPrinter(indent=4)
def my_safe_repr(object, context, maxlevels, level):
    typ = pprint._type(object)
    if typ is unicode:
        object = str(object)
    return pprint._safe_repr(object, context, maxlevels, level)
pp.format = my_safe_repr

class Hue: 
    def __init__(self,config): 
        hue_config = config['hue_config']
        self.username = hue_config['username']
        self.base_url = hue_config['url'] + hue_config['username'] + '/'
    def url_for(self, api): 
        return "{0}{1}/".format(self.base_url, api)
    def get_by_name(self, api, name): 
        print "Rules \n###########"
        p = re.compile(name, re.IGNORECASE)
        r = requests.get(self.url_for(api))
        response = r.json(); 
        for i in response:
            try:
                if  p.search(response[i]['name']):
                    print "##"
                    print "%s %s %s" % (i, response[i]['name'], response[i])
            except KeyError:
                pass
        print "###########"
    def get_scenes_by_name(self, name): 
        p = re.compile(name)
        r = requests.get(self.url_for('scenes'))
        response = r.json(); 
        for i in response:
            try:
                if  p.search(response[i]['name']):# and not response[i]['recycle']: 
                    print "%s %s %s" % (i, response[i]['name'], response[i])
            except KeyError:
                pass
    def get_info_from_rules(self): 
        r = requests.get(self.url_for('rules'))
        response = r.json(); 
        for i in response:
            for action in response[i]['actions']:
                try:
                    print "%s %s %s %s" % (i, response[i]['name'], response[i]['conditions'][0]['address'], action['body']['scene'])
                except KeyError:
                    pass
                try:
                    print "%s %s %s" % (i, response[i]['name'], action['address'])
                except KeyError:
                    pass
    def get_rules_for_sensor(self,sensor,delete=False): 
        p = re.compile('/sensors/{sensor}/'.format(sensor=sensor))
        r = requests.get(self.url_for('rules'))
        response = r.json(); 
        for i in response:
            if p.match(response[i]['conditions'][0]['address']):
                if delete:
                    r = requests.delete("{0}{1}".format(self.url_for('rules'), i))
                    print r.text
                else:
                    print i, response[i]['name']

class Room: 
    def __init__(self, room, hue):
        self.sensor = room['sensor']
        self.group = room['group']
        self.location = room['location']
        self.scenes = room['scenes']
        self.rule_generators = room['rules']
        self.schedule_generators = room['schedules']
        self.schedule_ids = {}
        self.hue = hue
    def delete_old_schedule_by_name(self, name):
        p = re.compile(name, re.IGNORECASE)
        r = requests.get(self.hue.url_for('schedules'))
        response = r.json(); 
        for i in response:
            if p.match(response[i]['name']):
                r = requests.delete("{0}{1}".format(self.hue.url_for('schedules'), i))
                print r.text
    def create_schedules(self, delete=False):
        for i in self.schedule_generators:
            schedule =  self.schedule_generators[i](self)
            if delete:
                self.delete_old_schedule_by_name(schedule['name'])
            r=requests.post(self.hue.url_for('schedules'), data=json.dumps(schedule))
            resp = r.json()
            self.schedule_ids[i] = resp[0]['success']['id']
    def create_sensor_rules(self):
        self.create_schedules(delete=True)
        self.hue.get_rules_for_sensor(self.sensor, delete=True)
        for i in self.rule_generators:
            rule = self.rule_generators[i](self)
            print rule
            # Deals with blank rules?
            if rule:
                rule['name']='{0}: {1}'.format(self.location,i)
                try: 
                    r=requests.post(self.hue.url_for('rules'), data=json.dumps(rule))
                    r.raise_for_status()
                    response = r.json()
                    try: 
                        response[0]['success']
                    except KeyError:
                        raise Exception(r.text)
                except Exception as e:
                    print r.status_code
                    print r.text
                    raise e
