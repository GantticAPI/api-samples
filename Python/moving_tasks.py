import json
import requests
from datetime import datetime, timedelta

PROJ_DF_ENDPOINT = 'https://planner.ganttic.com/api/v1/projects/datafields'
TASK_DF_ENDPOINT = 'https://planner.ganttic.com/api/v1/tasks/datafields'
PROJ_ENDPOINT = 'https://planner.ganttic.com/api/v1/projects'
TASKS_ENDPOINT = 'https://planner.ganttic.com/api/v1/tasks'
TASK_ENDPOINT = 'https://planner.ganttic.com/api/v1/task'

API_KEY = 'key123'

#region PROJ_DF
#Get project data fields to figure out which ones are milestones
#This bit doesn't need to be in the script and can be figures out beforehand

print('Fetching project data fields')

start_df_id = ''
end_df_id = ''

response = requests.get(url = PROJ_DF_ENDPOINT, params = {'token': API_KEY})

if response.status_code != 200:
    exit('Error fetching project data fields. Response status ' + str(response.status_code))

response_json = json.loads(response.text)

for data_field in response_json['dates']:
    if data_field['name'].lower() == 'start date': #correct name here
        start_df_id = data_field['id']
        print('Start milestone id is ' +  start_df_id)
    elif data_field['name'].lower() == 'end date': #correct name here
        end_df_id = data_field['id']
        print('End milestone id is ' + end_df_id)

#endregion

#region TASK_DF
#Get task data fields if tasks are marked with a status data field value
#This bit doesn't need to be in the script and can be figured out beforehand

print('Fetching task data fields')

task_status_df_id = ''
task_status_df_value_id = ''

response = requests.get(url = TASK_DF_ENDPOINT, params = {'token': API_KEY})

if response.status_code != 200:
    exit('Error fetching task data fields. Response status ' + str(response.status_code))

response_json = json.loads(response.text)

for data_field in response_json['listValues']:
    if data_field['name'].lower() == 'status': #correct name here
        task_status_df_id = data_field['id']
        print('Task status data field id is ' + task_status_df_id)
        for value in data_field['values']:
            if value['value'].lower() == 'planning': #correct name here
                task_status_df_value_id = value['id']
                print('Task status data field planning value is ' + task_status_df_value_id)

#endregion

#region PROJ
#Get projects to figure out which one you want to work with
#This bit doesn't need to be in the script, but it's unlikely that the user knows the project id,
#so it's possible to present them a list of all projects if used in a system with a UI

print('Fetching projects')

proj_id = ''
page = 0
page_count = 1

while page != page_count:
    response = requests.get(url = PROJ_ENDPOINT, params = {'token': API_KEY})

    if response.status_code != 200:
        exit('Error fetching projects. Response status ' + str(response.status_code))

    response_json = json.loads(response.text)

    if response_json['pageCount'] == 0:
        #Nothing returned
        break

    for project in response_json['items']:
        if project['name'].lower() == 'test': #correct name here
            proj_id = project['id']
            print('Project id is ' + proj_id)

    #Pagination
    page = response_json['page']
    page_count = response_json['pageCount']

#endregion

#region PROJ START/END
#This is only needed if going by start and end date. Merge with previous region if so.

print('Fetching projects')

start_date = ''
end_date = ''
page = 0
page_count = 1

while page != page_count:
    response = requests.get(url = PROJ_ENDPOINT, params = {'token': API_KEY})

    if response.status_code != 200:
        exit('Error fetching projects. Response status ' + str(response.status_code))

    response_json = json.loads(response.text)

    if response_json['pageCount'] == 0:
        #Nothing returned
        break

    for project in response_json['items']:
        if project['id'] == proj_id:
            for data_field in project['dataFields']['dates']:
                if data_field['id'] == start_df_id:
                    start_date = data_field['date']
                    print('Start date is ' + start_date)
                elif data_field['id'] == end_df_id:
                    end_date = data_field['date']
                    print('End date is ' + end_date)

    #Pagination
    page = response_json['page']
    page_count = response_json['pageCount']

#endregion

#region FETCH TASKS

print('Fetching tasks')

tasks = []
page = 0
page_count = 1

while page != page_count:
    #Use this to make a time based query
    response = requests.get(url = TASKS_ENDPOINT, params = {'token': API_KEY, 'projectId': proj_id, 'timeMin': start_date, 'timeMax': end_date})
    #Otherwise use this. timeMin and timeMax are still required, but make them arbitrarily large, reduce it to save processing time
    response = requests.get(url = TASKS_ENDPOINT, params = {'token': API_KEY, 'projectId': proj_id, 'timeMin': '2010-01-01', 'timeMax': '2030-01-01'})

    if response.status_code != 200:
        exit('Error fetching tasks. Response status ' + str(response.status_code))

    response_json = json.loads(response.text)

    if response_json['pageCount'] == 0:
        #Nothing returned
        break

    #If making a time based query then you want to modify all the returned tasks, since you have nothing else to go by
    for task in response_json['items']:
        #This takes all tasks that are strictly within start-end limits, but you can change accordingly if you also need tasks that partially fit inside the limits
        #Note that always end > start in task data, so no need to check for correctness in that, but project milestone values are not guaranteed,
        #so start_date > end_date is possible, since project data field values can be arbitrary even for milestones
        if task['start'] > start_date and task['end'] < end_date:
            tasks.append(task)

    #Else you have concrete markers for which tasks to change
    for task in response_json['items']:
        for data_field in task['dataFields']['listValues']:
            #Check that task data field value matches the status
            if data_field['id'] == task_status_df_id and data_field['valueId'] == task_status_df_value_id:
                tasks.append(task)

    #Pagination
    page = response_json['page']
    page_count = response_json['pageCount']

#endregion

#region MODIFY TASKS
#Finally modify the tasks that we filtered out from the bunch

print('Patching ' + str(len(tasks)) + ' tasks')

for task in tasks:
    modified_task = task
    #Change timedelta to correct value, possibly take from user input like command line args
    #https://docs.python.org/3/library/datetime.html#timedelta-objects
    modified_task['start'] = datetime.strftime(datetime.strptime(task['start'], '%Y-%m-%d %H:%M') + timedelta(days = 1), '%Y-%m-%d %H:%M')
    modified_task['end'] = datetime.strftime(datetime.strptime(task['end'], '%Y-%m-%d %H:%M') + timedelta(days = 1), '%Y-%m-%d %H:%M')

    response = requests.patch(url = TASK_ENDPOINT, params = {'token': API_KEY}, data = json.dumps(modified_task))

    if response.status_code != 200:
        print('Error modifying task. Response status ' + str(response.status_code))
        #Possibly add a user input check here like 'continue (y/n)?'
        #or an option to roll back changes for which you would need to store all the tasks that have already been modified
    else:
        print('Successfully modified task ' + task['id'])

#endregion

print('Done')