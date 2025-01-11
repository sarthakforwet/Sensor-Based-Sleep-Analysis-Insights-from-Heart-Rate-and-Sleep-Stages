# Importing libraries.
import numpy as np
import pandas as pd
import os
import pickle as pkl

# Load data from the pickle file.
def load_pickle(filename: str):
  '''
  Function to load data from a pickle file.
  Args:
    filename (str): Name of the pickle file.
  Returns:
    data: Loaded data from the pickle file.
  '''
  data = pd.read_pickle(filename)
  return data

# A) Load pod and vital patch files.
def load_pod_vital_files(path: str):
    '''
    Function to load pod and vital patch files from the provided dataset.
    Args:
        path (str): Path to directory containing data files.
    Returns:
        pod_files (dict): Dictionary containing pod data of subjects.
        vital_patch_files (dict): Dictionary containing vital patch data of subjects.
    '''
    pod_files = {}
    vital_patch_files = {}
    for file in os.listdir(path):
        if file.startswith('M'):
            continue

        if file.startswith('A'):
            vital_patch_files[file.split('_raw_results.pkl')[0]] = load_pickle(
                os.path.join(path, file))
        else:
            pod_data = load_pickle(os.path.join(path, file))
            user_id = pod_data['user_id']
            if user_id not in pod_files.keys():
                pod_files[user_id] = [pod_data]
            else:
                pod_files[user_id].append(pod_data)
    return pod_files, vital_patch_files

# B) Extract pod metrics.
def extract_pod_metrics(pod_data: dict):
    '''
    Function to extract key metrics from the Pod data.
    Args:
    pod_data (dict): Dictionary containing the Pod data.
    Returns:
        pod_df (pd.DataFrame): Extracted Pod metrics DataFrame.
        sleep_side (str): Sleep side used for measurement (left or right).
        user_id (str): User ID associated with the data.
    '''

    sleep_side = pod_data['side']
    user_id = pod_data['user_id']

    if sleep_side=='both':
        sleep_side = 'left' # Converting to left side when subject is sleeping in the middle.
    
    data = pod_data['metrics']

    # Filtering data to remove None values especially filtering the 5 minute heart rate. Also retaining the provided DataFrame.
    filtered = data[[f'{sleep_side}_hr', f'{sleep_side}_presence', f'{sleep_side}_sleep']].dropna().reset_index()

    # Renaming columns for convenience.
    pod_df = filtered.rename({f'{sleep_side}_hr':"heart_rate", f'{sleep_side}_presence':'presence', f'{sleep_side}_sleep':'sleep'}, axis=1)

    pod_df = pod_df[(pod_df['sleep']==1) & (pod_df['presence']==1)]

    # Initializing counter for storing consecutive timesteps.
    cons_timesteps = 0

    # Initializing sleep_start and sleep_end columns in the dataframe to default value of 0.
    pod_df['sleep_start'] = [0]*len(pod_df)
    pod_df['sleep_end'] = [0]*len(pod_df)

    # Storing the time difference between each consecutive pair of rows in the DataFrame.
    delta = (pod_df['ts'] - pod_df['ts'].shift(1)).apply(lambda x: x if x is pd.NaT else x.components[2])
    pod_df['timedelta'] = delta

    # Flag to ensure sleep_start always comes before sleep_end.
    flag = 1

    # Iterating through the DataFrame.
    for idx,row in pod_df.iterrows():
        if flag:
            # Increasing consecutive timestep by the time difference
            # while handling the initial case when time difference would be Null.
            cons_timesteps+=5 if row['timedelta'] is pd.NaT else row['timedelta']
            if cons_timesteps>=10:
                cons_timesteps = 0
                pod_df.loc[idx,'sleep_start'] = 1 # Changing sleep_start to True on 10 minutes consecutive sleeping on the bed.
                flag = 0

        if not flag:
            # Increasing consecutive timestep by the time difference
            # while handling the initial case when time difference would be Null.
            cons_timesteps+=5 if row['timedelta'] is pd.NaT else row['timedelta']
            if cons_timesteps>=20:
                pod_df.loc[idx-1,'sleep_end'] = 1 # (idx - 1) to handle the shift that we just made.
                cons_timesteps = 0
                flag = 1

    # Moving timestamps to index again for better working with timeseries data.
    pod_df.index = pod_df['ts']
    pod_df.drop('ts', axis=1, inplace=True)

    return pod_df, sleep_side, user_id

# C) Load vital patch variables.
def load_vital_patch_variables(vital_patch: dict):
    '''
    Function to load variables from the vital patch data.
    Args:
    vital_patch (dict): Dictionary containing the vital patch data.
    Returns:
    data (pd.DataFrame): Loaded vital patch variables DataFrame.
    '''
    data = vital_patch['vp_rr_intervals'].reset_index()
    data = data[['rr', 'datetime']]
    data = data.rename({'datetime':'ts'}, axis=1) # Renaming to match the column names in DataFrames for join.
    return data

# D) Calculate HR mean.
def calculate_hr_mean_vital(data):
    '''
    Function to calculate mean heart rate.
    Args:
    data (pd.DataFrame): Vital patch data.
    pod_data (pd.DataFrame): Pod data.
    Returns:
    hr_5min (pd.DataFrame): Vital patch heart rate averaged over 5-minute intervals.
    '''
    rr_1min = data.resample('1T', on='ts').count().reset_index() # Sampling rr per minute.
    hr_5min = rr_1min.resample('5T', on='ts').mean() # Taking mean of five 1-min samples aggregated together.
    hr_5min.rename({"rr":'hr'}, axis=1, inplace=True) # Renaming to make logical understanding.
    return round(hr_5min,2)

def output_hr_pod(pod_data):
    '''
    Function to output mean heart rate for the Pod.
    Args:
    pod_data (pd.DataFrame): Pod data.
    Returns:
    pod_hr_5min (pd.DataFrame): Pod heart rate over 5-minute intervals.
    '''
    pod_hr_5min = pod_data
    return pod_hr_5min

# E) Merge vital patch data with pod data for different nights.
def merge_vital_patch_pod(vital_patch: dict, master_filepath: str, vital_patch_files: dict, pod_files: dict):
    '''
    Function to merge the vital patch data with the pod data.
    Args:
    vital_patch (str): Vital patch filename.
    vital_patch_files (dict): Dictionary containing vital patch data of subjects.
    pod_files (dict): Dictionary containing pod data of subjects.
    master_filepath (str): Path to the master file containing user IDs.
    '''
    # Loading the master file to align the vital patch file to appropriate pod data for the user.
    master_df = pd.read_csv(master_filepath)

    # Loading the vital patch data using the function created above.
    vital_data = load_vital_patch_variables(vital_patch_files[vital_patch])

    # Getting the userId to further use it for saving the merged files.
    userId = master_df.loc[master_df['Vital Patch ID']==vital_patch]['User ID'].values[0]

    # Loop through the night(s) of the specific user.
    for data in pod_files[userId]:
        pod_df, sleep_side, user_id = extract_pod_metrics(data)

        # Calculating sleep_start and sleep_end variables.
        # Assigning the last timestamp value in the dataset if no sleep_end value encountered.
        # Another approach to imputing the sleep_end variable could be assigning it the timestamp of the most recent absence from the bed.
        sleep_start = pod_df[pod_df['sleep_start']==1].index[0]
        sleep_end = pod_df[pod_df['sleep_end']==1].index[0] if len(pod_df[pod_df['sleep_end']==1]) else pod_df.tail(1).index[0]
        
        # Calculating total duration of sleep.
        total_duration = (sleep_end - sleep_start)
        
        # Handling the case when total duration of sleep is less than four hours
        # or when it is greater than 11 hours.
        total_duration = total_duration.components[1]

        if total_duration>=4 and total_duration<=11:
            # Trimming timestamps of sleep from the pod DataFrame.
            pod_df = pod_df.loc[sleep_start:sleep_end]

            # Calculating the mean heart rate values for the vital patch data. 
            vital_hr_5min = calculate_hr_mean_vital(vital_data)

            # Outputting the heart rate values for the pod data.
            pod_hr_5min = output_hr_pod(pod_df)
            pod_hr_5min = pod_hr_5min.reset_index()
            
            # Sampling the vital patch data for mean heart rate to match the sleeping period of the pod data
            # to further merge both DataFrames.
            sample_mean_hr_df = vital_hr_5min.loc[sleep_start:sleep_end].reset_index()

            # Discovered that heart_rate in the dataset is of type object which
            # is changed to float64. 
            pod_hr_5min['heart_rate'] = pod_hr_5min['heart_rate'].astype('float64')

            # Merging DataFrames for pod data and vital patch sampled data for a particular night.
            df = pod_hr_5min.merge(sample_mean_hr_df, on="ts", how='left')

            # Adding variables to the data dictionary.
            data['merged_df'] = df # Adding merged dataframe.
            data['sleep_start'] = sleep_start # Adding sleep start information.
            data['sleep_end'] = sleep_end # Adding sleep end information.
            data['total_duration'] = total_duration # Adding total duration of sleep.

            # Storing the resultant dictionary object as a pickle file for later use.
            write_pickle(data, f"{vital_patch}_{userId}_{sleep_start}.pkl")

# F) Write To pickle files locally.
def write_pickle(obj: object, filename):
    '''
    Function to write provided objects to pickle files.
    Args:
        obj (object): The object to dump.
        filename (str): The filename in which to dump the obj. 
    '''
    pkl.dump(obj, open(filename, 'wb'))