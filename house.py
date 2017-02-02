import json
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


###

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


standard_rules = {
    'bright_hold':
        lambda self: {
            'actions': [
                {   'address': '/groups/{group}/action'.format(group=self.group),
                                  'body': {   'bri_inc': 30,
                                              'transitiontime': 9},
                                  'method': 'PUT'
                }
            ], 'conditions': [
                 {   'address': '/sensors/{sensor}/state/buttonevent'.
                                    format(sensor=self.sensor),
                                             'operator': 'eq',
                                             'value': '2001'
                 },
                 {   'address': '/sensors/{sensor}/state/lastupdated'.
                     format(sensor=self.sensor),
                                     'operator': 'dx'
                 }
            ],
             'recycle': False,
             'status': 'enabled'
        },
    'bright_short':
        lambda self: {
            'actions': [
                {
                    'address': '/groups/{group}/action'.
                        format(group=self.group),
                    'body': {   'scene': '{bright_scene}'.
                                    format(bright_scene=self.scenes['bright'])
                            },
                 'method': 'PUT'},
                {   'address': '/schedules/{off_schedule_id}'.
                        format(off_schedule_id=self.schedule_ids['off_schedule']),
                   'body': {   'status': 'disabled'},
                   'method': 'PUT'}
                ],
            'conditions': [
                {   'address': '/sensors/{sensor}/state/buttonevent'.
                        format(sensor=self.sensor),
                     'operator': 'eq',
                     'value': '2002'},
              {   'address': '/sensors/{sensor}/state/lastupdated'.
                  format(sensor=self.sensor),
              'operator': 'dx'}],
                        'recycle': False,
                        'status': 'enabled'},
    'dim_hold':
                lambda self: {
                    'actions': [
                        {   'address': '/groups/{group}/action'.format(group=self.group),
                                       'body': {   'bri_inc': -30,
                                                   'transitiontime': 9},
                                       'method': 'PUT'
                                       }
                        ],
                    'conditions': [
                        {   'address': '/sensors/{sensor}/state/buttonevent'.
                            format(sensor=self.sensor),
                                          'operator': 'eq',
                                          'value': '3001'
                                          },
                                      {   'address': '/sensors/{sensor}/state/lastupdated'.format(sensor=self.sensor),
                                          'operator': 'dx'}],
                    'recycle': False,
                    'status': 'enabled'
                    },
        'off_hold':
                    lambda self: {   'actions': [   {   'address': '/schedules/{off_schedule_id}'.format(
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

office_rules = standard_rules.copy()
# ADD a rule: During the day, we turn off all the lights (for leaving the house)
office_rules['off_hold_daylight'] = lambda self: {
                                    'actions': [   { 'address': '/groups/0/action',
                                   'body': {   'on': False, 'transitiontime': 60},
                                   'method': 'PUT'}],
                    'conditions': [   {   'address': '/sensors/{sensor}/state/buttonevent'.
                                            format(sensor=self.sensor),
                                          'operator': 'eq',
                                          'value': '4003'},
                                      {   'address': '/sensors/{sensor}/state/lastupdated'.
                                            format(sensor=self.sensor),
                                          'operator': 'dx'},
                                      {   'value': "true",
                                          'operator': 'eq',
                                          'address': '/sensors/1/state/daylight'
                                      }

                                      ],
                    'recycle': False,
                    'status': 'enabled'}


morning_scenes = [
        {
            'id': 'KxhYA9mvU7ttL49',
            'lightstates': {   '15': {   'bri': 1, 'on': True},
                               '18': {   'on': False},
                               '19': {   'on': False},
                               '4': {   'bri': 1, 'on': True}
            }
        }
]

afternoon_scenes = [
        {
            'id': 'KxhYA9mvU7ttL49',
            'lightstates': {   '15': {   'bri': 79, 'on': True},
                               '18': {   'on': False},
                               '19': {   'on': False},
                               '4': {   'bri': 59, 'on': True}
            }
        }
]
