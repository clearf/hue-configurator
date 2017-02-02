import json
import requests
import re
import pprint
import house
import hue

###
config = house.load_or_generate_config('./config')
myHue = hue.Hue(config)
#myHue.get_info_from_rules()
#myHue.get_by_name(name='bedroom', api='schedules')
#myHue.get_by_name(name='Torvald room', api='scenes')
#myHue.get_by_name(name='Office', api='scenes')
#myHue.get_by_name(name='Office', api='rules')
myHue.get_rules_for_sensor(3)


#office_schedules = standard_schedules.copy()
#office_schedules['on_schedule'] = xxx

office = hue.Room({
            'sensor': 3,
            'group': 2, 
            'location': "Office",
            'scenes': {'on': 'd258e36e1-on-0',
                'bright': 'd258e36e1-on-0'
                #'on_delay': 'OhBpAULnYeR6RPL'
            },
            'rules': house.office_rules,
            'schedules': house.standard_schedules
        }, myHue);
office.create_sensor_rules()

living_room = hue.Room({
            'sensor': 4,
            'group': 3, 
            'location': "Living Room",
            'scenes': {
                'on': 'db3fa697c-on-0',
                'bright': 'b74e4019a-on-0'
                },
            'rules': house.office_rules,
            'schedules': house.standard_schedules
        }, myHue);
living_room.create_sensor_rules()

bedroom = hue.Room({
            'sensor': 5,
            'group': 4, 
            'location': 'Bedroom',
            'scenes': { 
                'on': '8fd72847e-on-0',
                'bright': '4cd503ee8-on-0'
            },
            'rules': house.standard_rules,
            'schedules': house.standard_schedules
        }, myHue);
bedroom.create_sensor_rules()

# We have a second switch for the bedroom
bedroom.sensor=6
bedroom.create_sensor_rules()
