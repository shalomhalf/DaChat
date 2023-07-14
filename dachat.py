# Data Analysis on a WhatsApp Group Chat
##### *Author*: [ Shalom Halfon](https://www.linkedin.com/in/shalom-halfon2147/)

import re
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
os.sys.path.insert(0, os.path.abspath(".."))

def rawtodf(file, key, category):
    
    split_formats = {
        '12hr' : '\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APap][mM]\s-\s',
        '24hr' : '\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s',
        'custom' : ''
    }
    datetime_formats = {
        '12hr' : '%d/%m/%Y, %I:%M %p - ',
        '24hr' : '%d/%m/%Y, %H:%M - ',
        'custom': ''
    }
    
    with open(file, 'r', encoding='utf-8') as raw_data:
        raw_string = ' '.join(raw_data.read().split('\n'))
        user_msg = re.split(split_formats[key], raw_string) [1:]
        date_time = re.findall(split_formats[key], raw_string)
        
        df = pd.DataFrame({'date_time': date_time, 'user_msg': user_msg}) 
    df['date_time'] = pd.to_datetime(df['date_time'], format=datetime_formats[key])
    
    usernames = []
    msgs = []
    for i in df['user_msg']:
        a = re.split('([\w\W]+?):\s', i)
        if(a[1:]):
            usernames.append(a[1])
            msgs.append(a[2])
        else:
            usernames.append('group_notification')
            msgs.append(a[0])
        
    df['user'] = usernames
    df['category'] = category
    df['group'] = os.path.basename(file).split(".", 1)[0]
    df['message'] = msgs
    df['day_of_week'] = df['date_time'].dt.strftime('%a')
    df['day_of_month'] = df['date_time'].dt.day
    df['month'] = df['date_time'].dt.strftime('%b')
    df['year'] = df['date_time'].dt.year
    df['date'] = df['date_time'].apply(lambda x: x.date())
    df['hour'] = df['date_time'].apply(lambda x: x.hour)
    df['message_c'] = 1
    df.drop('user_msg', axis=1, inplace=True)
    
    return df
def file_verifier():
    global file
    while True:
        file = str(input('What is the file name?\n'))
        if not os.path.exists(file):
            print('Invalid path, try again\n')
            continue
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'Messages and calls are end-to-end encrypted' not in content:
                print('The file is not suitable for this application, try changing the WhatsApp settings to English and then export the information.')
                continue 
        break
def hour_formt_ver():
    global key
    key = str(input('hour formt? (12hr / 24hr)\n'))
    while key!= '12hr' and key !='24hr' :
        key = str(input('Please input only 12hr or 24hr\n'))
def n_verifier():
    global N
    while True:
        try:
            N = int(input('What is the number of participants in the group at the time the data was downloaded?\n'))
            break
        except ValueError:
            print('Not a valid number!')
def df_processing():
    global df , df_notification
    df_notification = (raw_df[raw_df['user']== 'group_notification']).copy()
    df_notification.reset_index(inplace=True)
    df_notification.drop(columns='index', inplace=True)
    df_notification['joined_by_link'] = (df_notification['message'].str.contains('joined')).astype(int)
    df_notification['added'] = (df_notification['message'].str.contains('added')).astype(int)
    df_notification['left'] = (df_notification['message'].str.contains('left')).astype(int)
    df_notification['n']= N
    df_notification['left_count']= 0

    for i in reversed(range(1,df_notification.shape[0])):
        df_notification.loc[i-1, 'n']= df_notification.iloc[i]['n']-df_notification.iloc[i]['joined_by_link']-df_notification.iloc[i]['added']+df_notification.iloc[i]['left']

    for i in range(1,df_notification.shape[0]):
        df_notification.loc[i,'left_count'] = df_notification.iloc[i-1]['left_count']+ df_notification.iloc[i]['left']

    df = (raw_df[raw_df['user']!= 'group_notification']).copy()
    day_of_creation = df_notification['date_time'].min()
    df_day1 = df['date_time'].min()
    df_end_day = df['date_time'].max()
    print('The group was established on {}, The database begins in {} and ends in {} '.format(day_of_creation.date(),
                                                                                          df_day1.date(),
                                                                                          df_end_day.date()))
    df_notification = df_notification[df_notification['date_time']> day_of_creation]
    df.reset_index(inplace=True)
    df.drop(columns='index', inplace=True)
    df['media_message'] = (df['message'] == '<Media omitted> ').astype(int)

if __name__ == "__main__":
    print('After Exported the chat from your WhatsApp to your computer, this software will convert it into two processed CSV files')
    
    file_verifier()
    
    hour_formt_ver()
    
    category = str(input('What is the group category? \n'))
    
    n_verifier()

    raw_df = rawtodf(file, key,category)
    
    df_processing()

    if os.path.isfile('results/fdf.csv')and os.path.isfile('fdf_notif.csv'):
        df.to_csv('results/fdf.csv', mode='a', header=False, index=False)
        df.to_csv('results/fdf_notif.csv', mode='a', header=False, index=False)
        print('Processed dfs have been added to the files no your computer')
    else:
        df.to_csv('results/fdf.csv', index=False)
        df_notification.to_csv('results/fdf_notif.csv', index=False)
        print('Processed csv files have been saved to your computer')