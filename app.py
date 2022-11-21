import requests, csv, argparse

def number_of_experiments():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id", help="paste your Project ID as the first argument")
    parser.add_argument("token", help="paste your Optimizely v2 REST API token as the second argument")
    args = parser.parse_args()
    project_id = args.project_id
    token = args.token
    
    MAX_RETRIES = 5
    change_count = 0
    changes_results = True
    changes_page = 1
    changes = []
    changes_call = "https://api.optimizely.com/v2/changes?project_id=" + project_id

    # get all changes from project
    while changes_results:
        print("Changes page:", changes_page)
        for _ in range(MAX_RETRIES):
            changes_results = requests.get(changes_call + "&per_page=100&page=%s" %changes_page, headers={"Authorization": "Bearer %s" % token})
            if changes_results.ok:
                changes_new_results = changes_results.json()
                changes.extend(changes_new_results)
                changes_page += 1
                break
    print("\nTotal changes:%s\n" %len(changes))
    
    count = 1
    if(len(changes)>0):
        with open("change_history_pull.csv", "w", newline="") as csvfile:
            fieldnames = ["Project_name","Campaign_name","Campaign_id","Change_type","Time_stamp","User_email","Entity_ui_url"]
            filewriter = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow(fieldnames) 
            
            #loop through each change
            for change in changes:
                if str(change["change_type"]) == "update":
                    if str(change["changes"][0]["property"]) == "status":
                        if str(change["entity"]["type"]) == "feature" or str(change["entity"]["type"]) == "experiment":
                            print(count,"- type:",change["entity"]["type"])
                            if (str(change["changes"][0]["after"]) == "running" and str(change["changes"][0]["before"]) == "paused") or (str(change["changes"][0]["after"]) == "paused" and str(change["changes"][0]["before"]) == "running"):
                                experiemnt_id = change["entity"]["id"]
                                experiment_call = "https://api.optimizely.com/v2/experiments/" + str(experiemnt_id)
                                experiment_result = requests.get(experiment_call, headers={"Authorization": "Bearer %s" % token})
                                if experiment_result.status_code == 200:
                                    experiment_result = experiment_result.json()
                                    if "production" in str(experiment_result["environments"]):
                                        campaign_id = experiment_result["campaign_id"]
                                        campaign_call = "https://api.optimizely.com/v2/campaigns/" + str(campaign_id)
                                        campaign_result = requests.get(campaign_call, headers={"Authorization": "Bearer %s" % token})
                                        project_id = change["project_id"]
                                        project_call = "https://api.optimizely.com/v2/projects/" + str(project_id)
                                        project_result = requests.get(project_call, headers={"Authorization": "Bearer %s" % token})
                                        if campaign_result.status_code == 200 and project_result.status_code == 200:
                                            campaign_result = campaign_result.json()
                                            campaign_name = campaign_result["name"]
                                            project_result = project_result.json()
                                            project_name = project_result["name"]
                                            # experiment is started
                                            if str(change["changes"][0]["after"]) == "running":
                                                filewriter.writerow([str(project_name), campaign_name, str(experiment_result["campaign_id"]), "Published", str(change["created"]), str(change["user"]["email"]), str(change["entity"]["ui_url"])])
                                                change_count += 1
                                            # experiment is paused
                                            elif str(change["changes"][0]["after"]) == "paused":  
                                                filewriter.writerow([str(project_name), campaign_name, str(experiment_result["campaign_id"]), "Paused", str(change["created"]), str(change["user"]["email"]), str(change["entity"]["ui_url"])])
                                                change_count += 1
                if change_count >= 5:
                    break
                count+=1
number_of_experiments() 
