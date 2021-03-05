import json
import requests

# RES_ENDPOINT = "https://planner.ganttic.com/api/v1/resources"
# DF_ENDPOINT = "https://planner.ganttic.com/api/v1/resources/datafields"
# TASK_ENDPOINT = "https://planner.ganttic.com/api/v1/tasks"

# API_KEY = "123"

RES_ENDPOINT = "https://www.yutiti.com/api/v1/resources"
DF_ENDPOINT = "https://www.yutiti.com/api/v1/resources/datafields"
TASK_ENDPOINT = "https://www.yutiti.com/api/v1/tasks"

API_KEY = "e315969af158c54f4846284750a6ad2a23f4318f37222f09362de41585377ceb"

resources = []

# Get the id of the data field
df_id = 0
df_value_id = 0
df_name = "team"
df_value_name = "field service"
value_found = False

response = requests.get(url = DF_ENDPOINT, params = {'token': API_KEY})

if response.status_code != 200:
    exit("Response status " + str(response.status_code))

response_json = json.loads(response.text)

for data_field in response_json['listValues']:
    if data_field['name'].lower() == df_name:
        df_id = data_field['id']
        for data_field_value in data_field['values']:
            if data_field_value['value'].lower() == df_value_name:
                df_value_id = data_field_value['id']
                value_found = True

                break

        if value_found:
            break

if df_id == 0 or df_value_id == 0:
    # Data field with the specified name not found
    exit("Data field named " + df_name + " not found or value named " + df_value_name + " not found.")

res_page = 1

# Get all resources
while True:
    res_response = requests.get(url = RES_ENDPOINT, params = {'token': API_KEY, 'page': res_page, 'includeEmptyDataFields': 1})

    res_json = json.loads(res_response.text)

    # Filter resources
    for resource in res_json['items']:
        for data_field in resource['dataFields']['listValues']:
            #Check to see if the data field exists on the resource
            if data_field['id'] == df_id and data_field['valueId'] == df_value_id:
                resources.append(resource)

                break

    # If last resource page
    if res_page == res_json['pageCount']:
        break
    else:
        res_page += 1

task_page = 1
start = '2021-01-01'
end = '2021-01-31'

# Get all resource tasks
for resource in resources:
    resource['utilizationPercent'] = 0
    resource['utilizationMinutes'] = 0

    while True:
        task_response = requests.get(url = TASK_ENDPOINT, params = {'token': API_KEY, 'page': task_page, 'timeMin': start, 'timeMax': end, 'resourceId': resource['id']})

        task_json = json.loads(task_response.text)

        # No tasks, resource utilization is 0
        if task_json['pageCount'] == 0:
            break

        for task in task_json['items']:
            if task['resourceUtilizationMinutes']:
                for util in task['resourceUtilizationMinutes']:
                    if util['resourceId'] == resource['id']:
                        resource['utilizationMinutes'] += util['utilizationMinutes']
            elif task['resourceUtilizationPercent']:
                # Depends on task work time
                resource['utilizationMinutes'] += 0

        # If last task page
        if task_page == task_json['pageCount']:
            break
        else:
            task_page += 1

for resource in resources:
    # Resource utilization % is resource utilization minutes * 100 / resource available work hours during the period
    print(resource['name'] + " - " + str(resource['utilizationMinutes']))