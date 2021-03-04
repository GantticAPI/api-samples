import json
import requests

RES_ENDPOINT = "https://planner.ganttic.com/api/v1/resources"
DF_ENDPOINT = "https://planner.ganttic.com/api/v1/resources/datafields"
TASK_ENDPOINT = "https://planner.ganttic.com/api/v1/tasks"

API_KEY = "123"

# Get the id of the data field
df_id = 0
df_name = "travel"

response = requests.get(url = DF_ENDPOINT, params = {'token': API_KEY})

response_json = json.loads(response.text)

if response.status_code != 200:
    exit(response_json)

for data_field in response_json['numbers']:
    if data_field['name'].lower() == df_name:
        df_id = data_field['id']

        break

if df_id == 0:
    # Data field with the specified name not found
    exit("Data field named " + df_name + " not found")

res_page = 1
task_page = 1

# Get all resources
while True:
    res_response = requests.get(url = RES_ENDPOINT, params = {'token': API_KEY, 'page': res_page, 'includeEmptyDataFields': 1})

    res_json = json.loads(res_response.text)

    # Filter resources
    for resource in res_json['items']:
        for data_field in resource['dataFields']['numbers']:
            #Check to see if the data field exists on the resource
            if data_field['id'] == df_id and data_field['number']:
                #Do things with resource data field
                print(resource['name'] + " - " + data_field['number'])

                break

        while True:
            task_response = requests.get(url = TASK_ENDPOINT, params = {'token': API_KEY, 'page': task_page, 'timeMin': '2021-01-01', 'timeMax': '2021-12-31', 'resourceId': resource['id']})

            task_json = json.loads(task_response.text)

            #No tasks
            if task_json['pageCount'] == 0:
                break

            for task in task_json['items']:
                #Do things with utilization
                print(task['utilizationPercent'])

            # If last task page
            if task_page == task_json['pageCount']:
                break
            else:
                task_page += 1



    # If last resource page
    if res_page == res_json['pageCount']:
        break
    else:
        res_page += 1
    