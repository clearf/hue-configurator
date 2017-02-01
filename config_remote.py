import json
import requests
import re
import pprint

pp = pprint.PrettyPrinter(indent=4)
def my_safe_repr(object, context, maxlevels, level):
    typ = pprint._type(object)
    if typ is unicode:
        object = str(object)
    return pprint._safe_repr(object, context, maxlevels, level)
pp.format = my_safe_repr


def load_or_generate_config(config_file):
    config={}
    try:
       with open(config_file, 'r') as f: 
          config=json.load(f)
          f.close()
    except IOError as e:
        print 'Using default config'
        config = {
                'hue_config': {
                    'url': 'http://192.168.1.51/api/',
                    'username': 'username'
                }
        }
        try: 
          # If the config file doesn't exist, write it
            print "Writing config to file"
            with open(config_file, 'w') as f:
              json.dump(config, f)
              f.close()
        except IOError as e:
          print "Unable to write config: ", e
    return config

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
        r = requests.get(hue.url_for('schedules'))
        response = r.json(); 
        for i in response:
            if p.match(response[i]['name']):
                r = requests.delete("{0}{1}".format(hue.url_for('schedules'), i))
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



###
config = load_or_generate_config('./config')


standard_schedules = {
        'off_schedule': lambda self: {   'autodelete': False,
            'command': {   'address': '/api/{username}/groups/{group}/action'.format(username=self.hue.username, group=self.group),
                           'body': {   'on': False, 'transitiontime': 6000},
                           'method': 'PUT'},
            'description': 'turn lamps slowly off',
            'localtime': 'PT00:05:00',
            'status': 'disabled',
            'name': '{location} slow off'.format(location=self.location)
        },
        'on_delay': lambda self: {   'autodelete': False,
                    'command': {   'address': '/api/{username}/groups/{group}/action'.format(username=self.hue.username, group=self.group),
                                   'body': {   'scene': self.scenes.get('on_delay', self.scenes['on'])},
                                   'method': 'PUT'},
                    'description': 'turn lamps slowly on',
                    'localtime': 'PT00:05:00',
                    'status': 'disabled',
                    'name': '{location} slow on'.format(location=self.location)
        }
    }


standard_rules = {   'bright_hold': lambda self: {   'actions': [   {   'address': '/groups/{group}/action'.format(group=self.group),
                                          'body': {   'bri_inc': 30,
                                                      'transitiontime': 9},
                                          'method': 'PUT'}],
                       'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.format(sensor=self.sensor),
                                             'operator': 'eq',
                                             'value': '2001'},
                                         {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                             'operator': 'dx'}],
                       'recycle': False,
                       'status': 'enabled'},
                'bright_short': lambda self: {   'actions': [   {   'address': '/groups/{group}/action'.format(group=self.group),
                                           'body': {   'scene': '{bright_scene}'.format(bright_scene=self.scenes['bright'])},
                                           'method': 'PUT'},
                                       {   'address': '/schedules/{off_schedule_id}'.format(off_schedule_id=self.schedule_ids['off_schedule']),
                                           'body': {   'status': 'disabled'},
                                           'method': 'PUT'}],
                        'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.format(sensor=self.sensor),
                                              'operator': 'eq',
                                              'value': '2002'},
                                          {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                              'operator': 'dx'}],
                        'recycle': False,
                        'status': 'enabled'},
                'dim_hold': lambda self: {   'actions': [   {   'address': '/groups/{group}/action'.format(group=self.group),
                                       'body': {   'bri_inc': -30,
                                                   'transitiontime': 9},
                                       'method': 'PUT'}],
                    'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.format(sensor=self.sensor),
                                          'operator': 'eq',
                                          'value': '3001'},
                                      {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                          'operator': 'dx'}],
                    'recycle': False,
                    'status': 'enabled'},
                'off_hold': lambda self: {   'actions': [   {   'address': '/schedules/{off_schedule_id}'.format(
                        off_schedule_id=self.schedule_ids['off_schedule']),
                                       'body': {   'status': 'enabled'},
                                       'method': 'PUT'}],
                    'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.format(sensor=self.sensor),
                                          'operator': 'eq',
                                          'value': '4003'},
                                      {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                          'operator': 'dx'}],
                    'recycle': False,
                    'status': 'enabled'},
                'off_short': lambda self: {   'actions': [   {   'address': '/groups/{group}/action'.format(group=self.group),
                                        'body': {   'on': False},
                                        'method': 'PUT'}],
                     'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.format(sensor=self.sensor),
                                           'operator': 'eq',
                                           'value': '4002'},
                                       {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                           'operator': 'dx'}],
                     'recycle': False,
                     'status': 'enabled'},
                'on_short': lambda self: {   'actions': [   {   'address': '/groups/{group}/action'.format(group=self.group),
                                       'body': {   'scene': '{on_scene}'.format(on_scene=self.scenes['on'])},
                                       'method': 'PUT'},
                                   {   'address': '/schedules/{off_schedule_id}'.format(off_schedule_id=self.schedule_ids['off_schedule']),
                                       'body': {   'status': 'disabled'},
                                       'method': 'PUT'}],
                    'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.format(sensor=self.sensor),
                                          'operator': 'eq',
                                          'value': '1002'},
                                      {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                          'operator': 'dx'}],
                    'recycle': False,
                    'status': 'enabled'}, 
                'on_hold': lambda self: {   'actions': [   
                                                   {   'address': '/schedules/{schedule_id}'.format(schedule_id=self.schedule_ids['on_delay']),
                                                       'body': {   'status': 'enabled'},
                                                       'method': 'PUT'}],
                                    'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.format(sensor=self.sensor),
                                                          'operator': 'eq',
                                                          'value': '1003'},
                                                      {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                                          'operator': 'dx'}],
                                    'recycle': False,
                                    'status': 'enabled'
                                }
            }

hue = Hue(config)
#hue.get_info_from_rules()
#hue.get_by_name(name='bedroom', api='schedules')
#hue.get_by_name(name='Torvald room', api='scenes')
#hue.get_by_name(name='Office', api='scenes')
#hue.get_by_name(name='Office', api='rules')
hue.get_rules_for_sensor(3)


#office_schedules = standard_schedules.copy()
#office_schedules['on_schedule'] = xxx

office_rules = standard_rules.copy()
# ADD a rule: During the day, we turn off all the lights (for leaving the house)
office_rules['off_hold_daylight'] = lambda self: {   
                                    'actions': [   { 'address': '/groups/0/action',
                                   'body': {   'on': False, 'transitiontime': 60},
                                   'method': 'PUT'}],
                    'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.format(sensor=self.sensor),
                                          'operator': 'eq',
                                          'value': '4003'},
                                      {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                          'operator': 'dx'},
                                      {   'value': "true",
                                          'operator': 'eq',
                                          'address': '/sensors/1/state/daylight'
                                      }
                                      
                                      ],
                    'recycle': False,
                    'status': 'enabled'}

office = Room({
            'sensor': 3,
            'group': 2, 
            'location': "Office",
            'scenes': {'on': 'd258e36e1-on-0',
                'bright': 'd258e36e1-on-0'
                #'on_delay': 'OhBpAULnYeR6RPL'
            },
            'rules': office_rules,
            'schedules': standard_schedules
        }, hue);
office.create_sensor_rules()
exit(0);

living_room = Room({
            'sensor': 4,
            'group': 3, 
            'location': "Living Room",
            'scenes': {
                'on': 'db3fa697c-on-0',
                'bright': 'b74e4019a-on-0'
                },
            'rules': office_rules,
            'schedules': standard_schedules
        }, hue);
living_room.create_sensor_rules()

bedroom = Room({
            'sensor': 5,
            'group': 4, 
            'location': 'Bedroom',
            'scenes': { 
                'on': '8fd72847e-on-0',
                'bright': '4cd503ee8-on-0'
            },
            'rules': standard_rules,
            'schedules': standard_schedules
        }, hue);
bedroom.create_sensor_rules()

# We have a second switch for the bedroom
bedroom.sensor=6
bedroom.create_sensor_rules()
