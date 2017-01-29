import json
import requests
import re

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
        self.base_url = hue_config['url'] + hue_config['username'] + '/'
        print self.base_url
    def get_rules_by_name(self, name): 

        print "Rules \n###########"
        p = re.compile(name, re.IGNORECASE)
        r = requests.get(self.base_url+'rules/')
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
        r = requests.get(self.base_url+'scenes/')
        response = r.json(); 
        for i in response:
            try:
                if  p.search(response[i]['name']):# and not response[i]['recycle']: 
                    print "%s %s %s" % (i, response[i]['name'], response[i])
            except KeyError:
                pass
    def get_info_from_rules(self): 
        r = requests.get(self.base_url+'rules/')
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
        r = requests.get(self.base_url+'rules/')
        response = r.json(); 
        for i in response:
            if p.match(response[i]['conditions'][0]['address']):
                if delete:
                    r = requests.delete(self.base_url+'rules/%s' % i)
                    print r.text
                else:
                    print i, response[i]['name']

class Room: 
    def __init__(self, room, hue):
        self.sensor = room['sensor']
        self.group = room['group']
        self.location = room['location']
        self.on_scene = room['on_scene']
        self.bright_scene = room['bright_scene']
        self.hue = hue
    def delete_old_schedules_by_name(self):
        p = re.compile('^{location} slow off$'.format(location=self.location))
        r = requests.get(hue.base_url+'schedules/')
        response = r.json(); 
        for i in response:
            if p.match(response[i]['name']):
                r = requests.delete(hue.base_url+'schedules/%s' % i)
                print r.text
    def create_off_schedule(self, delete=False):
        if delete:
            self.delete_old_schedules_by_name()
        schedule_string = """
        {{
                "name": "{location} slow off",
                "description": "turn lamps slowly off",
                "command": {{
                        "address": "/groups/{group}/action",
                        "body": {{
                                        "on": false,
                                        "transitiontime": 9000
                                }},
                                "method": "PUT"
                                }},
                "localtime": "PT00:01:00",
                "autodelete": false
        }}
        """.format(location=self.location, group=self.group)
        schedule = json.loads(schedule_string)
        r=requests.post(self.hue.base_url+'schedules/', data=json.dumps(schedule))
        resp = r.json()
        self.schedule_id = resp[0]['success']['id']
    def create_sensor_rules(self):
        self.create_off_schedule(delete=True)
        self.hue.get_rules_for_sensor(self.sensor, delete=True)
        sensor_string = """{{

            "on_press": {{
                "status": "enabled",
                "recycle": false,
                "conditions": [
                    {{
                        "address": "/sensors/{sensor}/state/buttonevent",
                        "operator": "eq",
                        "value": "1000"
                    }},
                    {{
                        "address": "/sensors/{sensor}/state/lastupdated",
                        "operator": "dx"
                    }}
                ],
                "actions": [
                    {{
                        "address": "/groups/{group}/action",
                        "method": "PUT",
                        "body": {{
                            "scene": "{on_scene}"
                        }}
                    }}
                ]
            }},

            "bright_short": {{
                "status": "enabled",
                "recycle": false,
                "conditions": [
                    {{
                        "address": "/sensors/{sensor}/state/buttonevent",
                        "operator": "eq",
                        "value": "2002"
                    }},
                    {{
                        "address": "/sensors/{sensor}/state/lastupdated",
                        "operator": "dx"
                    }}
                ],
                "actions": [
                    {{
                        "address": "/groups/{group}/action",
                        "method": "PUT",
                        "body": {{
                            "scene": "{bright_scene}"
                        }}
                    }}
                ]
            }},

            "bright_hold": {{
                "status": "enabled",
                "recycle": false,
                "conditions": [
                    {{
                        "address": "/sensors/{sensor}/state/buttonevent",
                        "operator": "eq",
                        "value": "2001"
                    }},
                    {{
                        "address": "/sensors/{sensor}/state/lastupdated",
                        "operator": "dx"
                    }}
                ],
                "actions": [
                    {{
                        "address": "/groups/{group}/action",
                        "method": "PUT",
                        "body": {{
                            "bri_inc": 30,
                            "transitiontime": 9
                        }}
                    }}
                ]
            }}, 


            "dim_hold": {{
                "status": "enabled",
                "recycle": false,
                "conditions": [
                    {{
                        "address": "/sensors/{sensor}/state/buttonevent",
                        "operator": "eq",
                        "value": "3001"
                    }},
                    {{
                        "address": "/sensors/{sensor}/state/lastupdated",
                        "operator": "dx"
                    }}
                ],
                "actions": [
                    {{
                        "address": "/groups/{group}/action",
                        "method": "PUT",
                        "body": {{
                            "bri_inc": -30,
                            "transitiontime": 9
                        }}
                    }}
                ]
            }},

            "off_short": {{
                "status": "enabled",
                "recycle": false,
                "conditions": [
                    {{
                        "address": "/sensors/{sensor}/state/buttonevent",
                        "operator": "eq",
                        "value": "4002"
                    }},
                    {{
                        "address": "/sensors/{sensor}/state/lastupdated",
                        "operator": "dx"
                    }}
                ],
                "actions": [
                    {{
                        "address": "/groups/{group}/action",
                        "method": "PUT",
                        "body": {{
                            "on": false
                        }}
                    }}
                ]
            }}, 

            "off_long": {{
                "status": "enabled",
                "recycle": false,
                "conditions": [
                    {{
                        "address": "/sensors/{sensor}/state/buttonevent",
                        "operator": "eq",
                        "value": "4003"
                    }},
                    {{
                        "address": "/sensors/{sensor}/state/lastupdated",
                        "operator": "dx"
                    }}
                ],
                "actions": [
                    {{
                        "address": "/schedules/{schedule}",
                        "method": "PUT",
                        "body": {{
                            "status": "enabled"
                        }}
                    }}
                ]
            }}
        }}""" .format(sensor=self.sensor, group=self.group, on_scene=self.on_scene, bright_scene=self.bright_scene, schedule=self.schedule_id)
        sensor_inputs = json.loads(sensor_string)

        for i in sensor_inputs:
            sensor_inputs[i]['name']='{0}: {1}'.format(self.location,i)
            try: 
                r=requests.post(self.hue.base_url+'rules/', data=json.dumps(sensor_inputs[i]))
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

hue = Hue(config)
#hue.get_info_from_rules()
hue.get_rules_by_name(name='living room')
#hue.get_rules_for_sensor(5)
exit(0)

living_room = Room({
            'sensor': 4,
            'group': 3, 
            'location': "Living Room",
            'on_scene': 'db3fa697c-on-0',
            'bright_scene': 'b74e4019a-on-0'
        }, hue);
#living_room.create_sensor_rules()

bedroom = Room({
            'sensor': 5,
            'group': 4, 
            'location': 'Bedroom',
            'on_scene': '8fd72847e-on-0',
            'bright_scene': '4cd503ee8-on-0'
        }, hue);
bedroom.create_sensor_rules()
