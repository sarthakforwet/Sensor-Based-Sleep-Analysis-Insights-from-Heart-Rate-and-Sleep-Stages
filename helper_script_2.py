# Importing libraries.
import helper_script_1 as hlp  # Using the first helper script to reuse functionality and avoid redundant code.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# A): Remove Outliers.
def remove_vital_patch_outliers(vital_patch: str, vital_patch_files: dict):
    '''
    Function to remove outliers from vital patch heart rate data.
    Outliers are defined as heart rates outside the range of 35 to 110 bpm inclusive.
    Args:
        vital_patch (str): Vital patch filename.
        vital_patch_files (dict): Dictionary containing vital patch data of subjects.
    Returns:
        pd.DataFrame: Dataframe with outliers replaced by NaN.
    '''
    data = hlp.load_vital_patch_variables(vital_patch_files[vital_patch])  # Getting patch data from first helper script.
    data = hlp.calculate_hr_mean_vital(data) # Calculating mean heart rate for vital patch for specific subject.
    data['hr'].loc[(data['hr'] <= 35) | (data['hr'] >= 110)] = pd.NaT # Removing outliers as directed.
    return data

def calculate_missing_data(vital_patch_files: dict):
    '''
    Function to calculate the number of outliers or % missing data for each night.
    This function prints the average % missing values, along with the minimum and maximum % missing data across all nights.
    It also identifies the subjects with the highest and lowest % missing data.
    Args:
        vital_patch_files (dict): Dictionary containing vital patch data for subjects.
    Returns:
        str: Subject ID with the lowest % missing data.
        str: Subject ID with the highest % missing data.
    '''
    min_sub = '' # String holding subject lowest % missing data.
    min_perc = 100
    max_sub = '' # String holding subject highest % missing data.
    max_perc = 0
    for vital_patch in vital_patch_files:
      userId = vital_patch.split('_')[1]
      print(f"Subject: {userId}")
      data = remove_vital_patch_outliers(vital_patch, vital_patch_files) # Removing outliers.

      missing_data = data.isnull().sum() / len(data) * 100
      avg_missing = missing_data.mean()
      min_missing = missing_data.min()
      max_missing = missing_data.max()

      print("Average % Missing Data: {:.2f}%".format(avg_missing))
      print("Minimum % Missing Data: {:.2f}%".format(min_missing))
      print("Maximum % Missing Data: {:.2f}%".format(max_missing))

      missing_data = missing_data.values[0]
      if missing_data <= min_perc:
        min_perc = missing_data
        min_sub = userId

      elif missing_data >= max_perc:
        max_perc = missing_data
        max_sub = userId

      print()

    return min_sub, max_sub

# B) Data Visualization and Correlation Plot.
def plot_correlation(base_path: str):
    '''
    Function to plot the correlation between ground truth ECG and Pod HR for each subject.
    Args:
        base_path (str): Base path to the files.
    '''
    for e in os.listdir(base_path):
        if e.startswith('A'):
            userId = e.split('_')[1]
            data = pd.read_pickle(e)

            fig, ax = plt.subplots()

            sns.scatterplot(data=data, x='hr', y='heart_rate', ax=ax)
            sns.lineplot(data=data, x='hr', y='hr', color='red', ax=ax)

            corr_coef = data['hr'].corr(data['heart_rate']) # Calculating the pearson's coefficient.
            ax.annotate('r value = {:.2f}'.format(corr_coef), xy=(0.05, 0.95), xycoords='axes fraction', fontsize=12)

            plt.title(f'Correlation between Ground Truth ECG and Pod HR for {userId}')
            plt.show() # Showing the plot which can also be returned after certain modifications if required.

# Additional Plot.
def plot_sleep_stage_hr(pod_file: str, title):
  '''
  Function to plot a histogram of heart rate in different sleep stages.
  Data retrieved from pod only.
  Args:
    pod_file (str): filename containing pod data.
  '''
  pod_data = pd.read_pickle(pod_file)

  sleep_side = pod_data['side']
  pod_df = pod_data['metrics'][[f'{sleep_side}_hr', f'{sleep_side}_stage']] # Retrieving information about heart rate and sleep stage.
  pod_df.rename({f'{sleep_side}_hr':'hr', f"{sleep_side}_stage":"stage"}, axis=1, inplace=True) # Renaming columns for convenience.
  pod_df = pod_df.dropna() # Removing null values from the data. (5 minute sampling of heart rate).

  # Grouping by different sleep stages and plotting corresponding heart rate.
  pod_df.groupby('stage')['hr'].plot.hist(legend=True, alpha=0.7, edgecolor='white')
  plt.xlabel("heart rate")
  plt.title(title)
  plt.show()
