import pandas as pd
def state_population(population, state_name):
    population = population[population['State'] == state_name]
    return population['population'].sum()

def state_weekly_stats(dataframe, state_name):
    import pandas as pd
    # Filter dataframe for the state and save first four columns 
    state_deaths = dataframe[dataframe['State'] == state_name]
    state_columns = state_deaths.iloc[:, :4]
    
    # Select date columns only
    state_deaths_only = state_deaths.drop(columns=['countyFIPS', 'County Name', 'State', 'StateFIPS'])
    # Make sure dates are in datetime format
    state_deaths_only.columns = pd.to_datetime(state_deaths_only.columns, format='%Y-%m-%d', errors='coerce')
    # Filter for selected range
    state_deaths_only = state_deaths_only.loc[:, (state_deaths_only.columns >= '2020-06-01') & (state_deaths_only.columns <= '2021-01-03')]
    
    # Empty DataFrame to hold stats
    weekly_death_stats = pd.DataFrame()
    
    # Create weekly date ranges
    weekly_groups = pd.date_range(start='2020-06-01', end='2021-01-03', freq='W-SUN')

    # For loop to iterate over weeks and calculate stats for deaths
    for i, week_end in enumerate(weekly_groups):
        # Select the date range for the week
        week_start = week_end - pd.Timedelta(days=6)

        # Select the columns corresponding to the week
        week_columns_deaths = state_deaths_only.loc[:, (state_deaths_only.columns >= week_start) & (state_deaths_only.columns <= week_end)]
        
        # Calculate mean, median, and mode for each county (row) across the week (columns)
        weekly_death_mean = week_columns_deaths.mean(axis=1)
        weekly_death_median = week_columns_deaths.median(axis=1)
        weekly_death_mode = week_columns_deaths.mode(axis=1)[0]  # Pick the first mode 

        # Store the results in the DataFrame
        weekly_death_stats[f'week_{i+1}_mean'] = weekly_death_mean
        weekly_death_stats[f'week_{i+1}_median'] = weekly_death_median
        weekly_death_stats[f'week_{i+1}_mode'] = weekly_death_mode

    weekly_death_stats = pd.concat([state_columns, weekly_death_stats], axis=1)

    
    return weekly_death_stats

def statewide_stats(cases, deaths, state_name):
    # Calls state_weekly_stats to get weekly case and death stats
    weekly_case_stats = state_weekly_stats(cases, state_name)
    weekly_death_stats = state_weekly_stats(deaths, state_name)
    # Combine both stats for the state
    state_county_weekly = pd.concat([weekly_case_stats, weekly_death_stats], axis=1)

    # Create empty dataframe to hold stats
    statewide_weekly_stats = pd.DataFrame()
    
    # weekly date range
    weekly_groups = pd.date_range(start='2020-06-01', end='2021-01-03', freq='W-SUN')

    for i in range(len(weekly_groups)):
        statewide_mean = weekly_case_stats[f'week_{i+1}_mean'].mean()
        statewide_median = weekly_case_stats[f'week_{i+1}_median'].median()
        statewide_mode = weekly_case_stats[f'week_{i+1}_mode'].mode()[0]

        statewide_death_mean = weekly_death_stats[f'week_{i+1}_mean'].mean()
        statewide_death_median = weekly_death_stats[f'week_{i+1}_median'].median()
        statewide_death_mode = weekly_death_stats[f'week_{i+1}_mode'].mode()[0]

        statewide_weekly_stats = pd.concat([statewide_weekly_stats, pd.DataFrame({
            'Week': [f'{i+1}'],
            'Statewide Case Mean': [statewide_mean],
            'Statewide Case Median': [statewide_median],
            'Statewide Case Mode': [statewide_mode],
            'Statewide Death Mean': [statewide_death_mean],
            'Statewide Death Median': [statewide_death_median],
            'Statewide Death Mode': [statewide_death_mode]
        })], ignore_index=True)

    return statewide_weekly_stats

def weekly_sum(dataframe,state_name):
    state_df = dataframe[dataframe['State'] == state_name]
    state_df.columns = pd.to_datetime(state_df.columns, format='%Y-%m-%d', errors='coerce')
    
    weekly_groups = pd.date_range(start='2020-06-01', end='2021-01-03', freq='W-SUN')
    # Empty dataframe to hold values
    weekly_sums = pd.DataFrame()
    
    for week_end in weekly_groups:
        # Define the start of the week
        week_start = week_end - pd.Timedelta(days=6)
    
        # Select week in the date columns 
        week_columns = state_df.loc[:, (state_df.columns >= week_start) & (state_df.columns <= week_end)]
    
        # Sum across rows then sum again
        weekly_total = week_columns.sum().sum()  
        
        weekly_sum_df = pd.DataFrame([weekly_total], index=[week_end], columns=[f'{state_name} Weekly Total'])

        # Concatenate the new DataFrame to the weekly_sums DataFrame
        weekly_sums = pd.concat([weekly_sums, weekly_sum_df])

    
    weekly_sums = pd.concat([weekly_sums, weekly_sum_df])

    return weekly_sums

def case_normalization(state_name):
    NORM_FACTOR = 10000
    case_sum = weekly_sum(cases, state_name)

    # Reset the index and rename it to 'Week'
    case_sum = case_sum.reset_index().rename(columns={'index': 'Week'})

    # List to store the totals
    totals = [] 

    # Iterate over the case_sum DataFrame to normalize the values
    for i, row in case_sum.iterrows():
        # Normalize by population and multiply by NORM_FACTOR
        norm_value = ((row[f'{state_name} Weekly Total']) / state_population(population, state_name)) * NORM_FACTOR
        totals.append(norm_value)

    # Add the normalized series to case_sum DataFrame
    case_sum[f'{state_name} Normalization'] = totals
    return case_sum


def death_normalization(state_name):
    NORM_FACTOR = 10000
    death_sum = weekly_sum(deaths, state_name)

    # Reset the index and rename it to 'Week'
    death_sum = death_sum.reset_index().rename(columns={'index': 'Week'})

    # List to store the totals
    totals = [] 

    # Iterate over the case_sum DataFrame to normalize the values
    for i, row in death_sum.iterrows():
        # Normalize by population and multiply by NORM_FACTOR
        norm_value = ((row[f'{state_name} Weekly Total']) / state_population(population, state_name)) * NORM_FACTOR
        totals.append(norm_value)

    # Add to death_sum
    death_sum[f'{state_name} Normalization'] = totals
    return death_sum
    
def sum_by_county_weekly(df,state):
    state_cases = df[df['State'] == state]
    columns = state_cases.iloc[:, :4]
    state_cases = state_cases.loc[:, (state_cases.columns >= '2020-06-01') & (state_cases.columns <= '2021-01-03')]
    state_cases = pd.concat([columns, state_cases], axis=1)
    state_cases = state_cases.reset_index(drop=True)
    
    # Create a new DataFrame for the result
    summed_df = pd.DataFrame()
    
    # Copy columns
    summed_df['countyFIPS'] = state_cases['countyFIPS']
    summed_df['County Name'] = state_cases['County Name']
    
    # Get the columns representing the weekly data
    weekly_data = state_cases.iloc[:, 4:] 
    
    # Number of weeks (sum every 7 days)
    num_weeks = weekly_data.shape[1] // 7
    
    # Loop over the weeks and sum 7 columns at a time
    for week in range(num_weeks):
        start = week * 7
        end = start + 7
        week_label = f'Week {week + 1}' 
        summed_df[week_label] = weekly_data.iloc[:, start:end].sum(axis=1)
        
    summed_df= summed_df.drop(summed_df.index[0]).reset_index(drop=True)
    return summed_df