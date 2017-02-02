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
#myHue.get_by_name(name='Bedroom', api='scenes')
#myHue.get_by_name(name='Office', api='rules')
#myHue.get_rules_for_sensor(3)

myHue.get_scene('KxhYA9mvU7ttL49')
myHue.update_scenes(house.afternoon_scenes)
myHue.get_scene('KxhYA9mvU7ttL49')
