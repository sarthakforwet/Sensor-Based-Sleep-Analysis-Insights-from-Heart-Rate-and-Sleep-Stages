# Sensor-Based Sleep Analysis: Insights from Heart Rate and Sleep Stages

This project processes and analyzes multi-night sensor data to provide insights into sleep quality using metrics such as heart rate and sleep stages. By handling missing data and identifying correlation patterns, this analysis delivers a comprehensive view of users' sleep and physiological health.

## Table of Contents
- [Overview](#overview)
- [Data Sources](#data-sources)
- [Objectives](#objectives)
- [Approach](#approach)
- [Results](#results)
- [Usage](#usage)
- [Future Work](#future-work)

## Overview
With a growing interest in quantifying sleep quality through physiological metrics, this project utilizes wearable sensor data, including heart rate and sleep stage information, to analyze sleep patterns across multiple nights for over 100 users. Key metrics and visualizations enable a clearer understanding of users' overall sleep health.

## Data Sources
- **Pod Files**: Contain nightly sleep metrics for each user.
- **Vital Patch Files**: Provide heart rate and related physiological data.

## Objectives
- Process raw sensor data and clean for analysis.
- Calculate key metrics, including average heart rate and sleep stage duration.
- Address missing data to ensure analysis reliability.
- Visualize correlation patterns between sleep stages and physiological metrics.

## Approach
1. **Data Preprocessing**: Loaded and cleaned pod and vital patch files for consistent data formatting.
2. **Metric Calculation**: Computed average heart rate, total sleep duration, and stage-specific metrics.
3. **Data Integration**: Merged multi-night data by subject ID, handling missing values to maintain a 95% data retention rate.
4. **Analysis & Visualization**: Analyzed correlations and patterns across sleep stages and heart rate; visualized results to highlight trends.

## Results
- **Data Completeness**: Retained 95% of data across nights and users.
- **Correlation Patterns**: Identified relationships between heart rate and specific sleep stages.
- **Insights**: Provided a clear representation of how physiological health metrics align with sleep quality, aiding in further analysis of sleep health.


## Usage
Add your data files to the appropriate folder.
Run the analysis notebook Eight_Sleep_Assessment.ipynb to process the data and generate metrics.
Review the generated CSV and visualization outputs for insights.

## Future Work
- Expand Analysis: Incorporate additional physiological metrics, such as respiratory rate and temperature.
- Advanced Modeling: Use machine learning to predict sleep quality and disturbances.
- Interactive Dashboard: Develop a user-friendly interface for real-time data visualization and analysis.