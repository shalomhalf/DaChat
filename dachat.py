# Data Analysis on a WhatsApp Group Chat
##### *Author*: [ Shalom Halfon](https://www.linkedin.com/in/shalom-halfon2147/)
##### [*GitHub*](https://github.com/shalomhalf/DaChat) 

import re
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import os.path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox

os.sys.path.insert(0, os.path.abspath('..'))


def rawtodf(file, category):
    
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
    def hour_format(file_path):
        raw = open(file_path, 'r', encoding='utf-8')
        content = raw.read()
        if bool(re.search(split_formats.get('12hr'), content)):
            return '12hr'
        elif bool(re.search(split_formats.get('24hr'), content)):
            return '24hr'
        else:
            tk.messagebox.showwarning(title='Invalid Input', message='txt file hour format doesnt match!')
    key = hour_format(file)
    with open(file, 'r', encoding='utf-8') as raw_data:
        raw_string = ' '.join(raw_data.read().split('\n')) # converting the list split by newline char. as one whole string as there can be multi-line messages
        user_msg = re.split(split_formats[key], raw_string) [1:] # splits at all the date-time pattern, resulting in list of all the messages with user names
        date_time = re.findall(split_formats[key], raw_string) # finds all the date-time patterns
        
        df = pd.DataFrame({'date_time': date_time, 'user_msg': user_msg}) # exporting it to a df
        
    # converting date-time pattern which is of type String to type datetime,
    # format is to be specified for the whole string where the placeholders are extracted by the method 
    df['date_time'] = pd.to_datetime(df['date_time'], format=datetime_formats[key])
    
    # split user and msg 
    usernames = []
    msgs = []
    for i in df['user_msg']:
        a = re.split('([\w\W]+?):\s', i) # lazy pattern match to first {user_name}: pattern and spliting it aka each msg from a user
        if(a[1:]): # user typed messages
            usernames.append(a[1])
            msgs.append(a[2])
        else: # other notifications in the group(eg: someone was added, some left ...)
            usernames.append('group_notification')
            msgs.append(a[0])

    # creating new columns         
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
    # dropping the old user_msg col.
    df.drop('user_msg', axis=1, inplace=True)
    
    return df
def df_processing(raw_df , n):
    df_notification = (raw_df[raw_df['user']== 'group_notification']).copy()
    df_notification.reset_index(inplace=True)
    df_notification.drop(columns='index', inplace=True)
    df_notification['joined_by_link'] = (df_notification['message'].str.contains('joined')).astype(int)
    df_notification['added'] = (df_notification['message'].str.contains('added')).astype(int)
    df_notification['left'] = (df_notification['message'].str.contains('left')).astype(int)
    df_notification['n']= n
    df_notification['left_count']= 0

    for i in reversed(range(1,df_notification.shape[0])):
        df_notification.loc[i-1, 'n']= df_notification.iloc[i]['n']-df_notification.iloc[i]['joined_by_link']-df_notification.iloc[i]['added']+df_notification.iloc[i]['left']

    for i in range(1,df_notification.shape[0]):
        df_notification.loc[i,'left_count'] = df_notification.iloc[i-1]['left_count']+ df_notification.iloc[i]['left']

    df = (raw_df[raw_df['user']!= 'group_notification']).copy()
    day_of_creation = df_notification['date_time'].min()
    df_day1 = df['date_time'].min()
    df_end_day = df['date_time'].max()
    df_notification = df_notification[df_notification['date_time']> day_of_creation]
    df.reset_index(inplace=True)
    df.drop(columns='index', inplace=True)
    df['media_message'] = (df['message'] == '<Media omitted> ').astype(int)
    return df , df_notification, day_of_creation
def group_by_day(df, df_notification):
    date_group = df.copy()
    date_group.drop(columns=['user', 'category', 'group', 'message', 'day_of_week','year','day_of_month','hour'], inplace=True)
    date_group = date_group.groupby('date').sum(numeric_only=True)
    idx = pd.date_range(date_group.index.min(), date_group.index.max())
    date_group = date_group.reindex(idx).fillna(0)
    date_n_group = df_notification.copy()
    date_n_group.drop(columns=['year',"day_of_month","year","hour", "message_c","joined_by_link","added","left"], inplace=True)
    date_n_group = date_n_group.groupby('date').mean(numeric_only=True)
    idx = pd.date_range(date_n_group.index.min(), date_n_group.index.max())
    date_n_group = date_n_group.reindex(idx).fillna(method="ffill")
    date_al_group = df_notification.copy()
    date_al_group.drop(columns=['year',"day_of_month","year","hour", "message_c","n","left_count"], inplace=True)
    date_al_group = date_al_group.groupby('date').sum(numeric_only=True)
    idx = pd.date_range(date_al_group.index.min(), date_al_group.index.max())
    date_al_group = date_al_group.reindex(idx).fillna(0)
    date_group =pd.concat([date_n_group,date_group,date_al_group],axis=1)
    date_group["engagement"]=date_group["message_c"]/date_group["n"]
    return date_group
def plot_data(df ,date_group, raw_df, day_of_creation):
    col = sns.color_palette('Dark2')
    hour = [6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,0,1,2,3,4,5]
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    j_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    def top_10_active_days():
        sns.set_style('whitegrid')
        plt.fontsize = 10
        plt.figure(figsize = (13,6))
        top10days = date_group.sort_values(by='message_c', ascending=False).head(10)
        sns.barplot(data=top10days, x=top10days.index.date, y='message_c', color = col[0])
        plt.title('Top 10 most active days')
        plt.ylabel('Message Count')
        plt.xticks(rotation=15)
        plt.savefig('plots/top_10_active_days.png', format = 'png')
    
    top_10_active_days()

    def top_10_active_users():
        top10df = df.groupby('user')['message_c'].sum().sort_values(ascending=False).head(10).reset_index()
        sns.set_style('whitegrid')
        plt.fontsize = 10
        plt.figure(figsize = (10 , 4.4))
        plt.bar(top10df['user'], top10df['message_c'], color = col[0])
        plt.xticks(rotation=15)
        plt.ylabel('Message Count')
        plt.title('Top 10 Most Active Users ')
        plt.savefig('plots/top_10_active_users.png', format = 'png')
    top_10_active_users()
    
    def top_10_media_sharing():
        sns.set_style('whitegrid')
        plt.fontsize = 10
        plt.figure(figsize = (13,6))
        top10media = df.groupby('user')['media_message'].sum().sort_values(ascending=False).head(10).reset_index()
        plt.bar(top10media['user'], top10media['media_message'], color = col[0])
        plt.xticks(rotation=15)
        plt.ylabel('Message Count')
        plt.title('Top 10 Media Sharing Users')
        plt.savefig('plots/top_10_media_sharing.png', format = 'png')
    top_10_media_sharing()

    def active_hours():
        sns.set_style('whitegrid')
        plt.fontsize = 10
        plt.figure(figsize = (13,6))
        grouped_by_time = df.groupby('hour').sum(numeric_only=True).reset_index().sort_values(by = 'hour')
        sns.barplot(x =grouped_by_time['hour'],y= grouped_by_time['message_c'] ,order=hour , color = col[0])
        plt.title('Most Active Hours')
        plt.ylabel('Message Count')
        plt.xticks(rotation=0)
        plt.xlabel('')
        plt.savefig('plots/active_hours.png', format = 'png')
    active_hours()

    def day_of_week():
        sns.set_style('whitegrid')
        plt.fontsize = 10
        plt.figure(figsize = (13,6))
        grouped_by_day = df[['day_of_week', 'message_c']].groupby('day_of_week').sum(numeric_only=True).reset_index()
        sns.barplot(x=grouped_by_day['day_of_week'], y= grouped_by_day['message_c'], order=days, color=col[0])
        plt.ylabel('Message Count')
        plt.xlabel('')
        plt.title('Total Messages sent by Day of Week')
        plt.savefig('plots/day_of_week.png', format = 'png')
    day_of_week()

    def month_group():
        sns.set_style('whitegrid')
        plt.fontsize = 10
        plt.figure(figsize = (13,6))
        grouped_by_month = df[['month', 'message_c']].groupby('month').sum(numeric_only=True).reset_index()
        sns.barplot(x=grouped_by_month['message_c'], y = grouped_by_month['month'] , order = months, color=col[0])
        plt.ylabel('')
        plt.xlabel('Message Count')
        plt.xticks()
        plt.title('Total messages sent grouped by Month')
        plt.savefig('plots/month_group.png', format = 'png')
    month_group()

    def dh_heatmap():
        sns.set_style('white')
        plt.fontsize = 10
        plt.figure(figsize = (13,6))
        group_by_day_and_hour = df.groupby(['day_of_week', 'hour']).sum(numeric_only=True).reset_index()
        group_by_day_and_hour.drop(columns='year', inplace=True)
        pt = group_by_day_and_hour.pivot_table(index = 'hour', columns = 'day_of_week', values = 'message_c').reindex(index = hour, columns = days)
        sns.heatmap(pt.fillna(0) , cmap = 'viridis', cbar_kws={'label': 'Message Count'})
        plt.ylabel('Hour')
        plt.xlabel('Day of Week')
        plt.title('Heatmap of Message Count by Day and Hour')
        plt.savefig('plots/dh_heatmap.png', format = 'png')
    dh_heatmap()

    def traffic():
        sns.set_style('white')
        plt.fontsize = 20
        plt.figure(figsize = (16, 6))
        plt.bar(date_group.index, height = date_group['message_c'], color= col[2] ,label='Daily Message Count', alpha = 0.4)
        plt.plot(date_group.index,date_group['message_c'].rolling(30).mean(), color= col[2] ,label='Monthly Rolling Average')
        plt.legend()
        plt.title('Messages over time aka Traffic over time')
        plt.ylabel('Message Count')
        plt.xlabel('Time')
        plt.set_cmap('Accent')
        plt.savefig('plots/traffic.png', format = 'png')
    traffic()
    
    def bar_leav_join():
        sns.set_style('white')
        plt.fontsize = 20
        plt.figure(figsize = (16, 6))
        plt.bar(date_group.index, height = date_group['joined_by_link']+date_group['added'] ,width=2 ,label='added Participants', color=col[0])
        plt.bar(date_group.index, height = (date_group["left"])*-1 ,width=2.5 ,label='Leaveing Participants', color=col[1])
        plt.legend()
        plt.title('Participants Leaveing and Joining the group over time')
        plt.ylabel('Count')
        plt.xlabel('Time')
        plt.savefig('plots/bar_leav_join.png', format = 'png')
    bar_leav_join()

    def line_leav_join():
        sns.set_style('white')
        plt.fontsize = 20
        plt.figure(figsize = (16, 6))
        plt.plot(date_group.index,date_group['n']-(date_group['n'][0]) ,label='joining', color=col[0])
        plt.plot(date_group.index,date_group['left_count'] ,label='leaving', color=col[1])
        plt.title('Participants leaving & Number of Participants joining over time')
        plt.ylabel('Count')
        plt.xlabel('Time')
        plt.legend(labels=['joining', 'leaving'])
        plt.savefig('plots/line_leav_join.png', format = 'png')
    line_leav_join()

    def engagement():
        sns.set_style('white')
        plt.fontsize = 20
        fig, ax1 = plt.subplots(figsize = (16, 6))
        ax1 = sns.lineplot(data=date_group, x=date_group.index , y='n', label='Participants Count',color=col[0])
        ax2 = ax1.twinx()
        sns.lineplot(data=date_group, x=date_group.index , y=(date_group['message_c']/date_group['n']).rolling(30).mean(),
                     color=col[3],
                     ax=ax2, label='Engagement Rolling Average')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Count')
        ax2.set_ylabel('Rate')
        plt.title('Participants Count VS Engagement Rate over time')
        plt.savefig('plots/engagement.png', format = 'png')
    engagement()

    def leav_traffic():
        sns.set_style('white')
        plt.fontsize = 20
        fig, ax1 = plt.subplots(figsize = (18, 6))
        ax1.plot(date_group.index,date_group['message_c'], color= col[2] , alpha=0.6 ,label='Daily Messages')
        ax2 = ax1.twinx()
        ax2.bar(date_group.index, height = date_group['left'] ,width = 1.5 , alpha=1 ,label='left Count', color=col[1])
        plt.title('Message Count Vs Participants leaving the group over time')
        ax1.legend(loc = 2)
        ax2.legend(loc = 1)
        ax1.set_ylabel('Message Count')
        ax2.set_ylabel('Left Count')
        ax1.set_xlabel('Time')
        plt.savefig('plots/leav_traffic.png', format = 'png')
    leav_traffic()

    title = '{} Group Chat Analysis'.format(df["group"][0])
    df_day1 = raw_df['date_time'].min()
    df_end_day = df['date_time'].max()
    info_1 = '"{}" group chat was established on {}, The chat database begins in {} and ends in {}.'.format(df['group'][0], day_of_creation.date(),
                                                                                                                                                                                                                df_day1.date(), df_end_day.date())
    info_2 = 'Total number of people who have sent at least one message on the group is {}'.format(len(df.user.unique()) - 1)
    info_3 = '{} of all messages in the group were sent with a picture.'.format(round(df['media_message'].mean()*100,1))
    info_4 = 'This analysis was created using \nMore information can be found here.'

    class PDF(FPDF):
        def header(self):
            self.image('images/logo.png', 10, 8, 25)
            self.set_font('Helvetica', 'B', 20)
            self.cell(0, 10, title, border=False, align="C")
            self.ln(20)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 10)
            self.set_text_color(169, 169, 169)
            self.cell(0, 10, f'Page {self.page_no()}' , align="C")

        def content(self, c):
            self.set_font('Helvetica', '', 10)
            self.multi_cell(pdf.w - 10, 5, c)
            self.ln()
        
    pdf = PDF('P', 'mm', 'Letter')    
    pdf.set_title(title)
    pdf.set_author('DaChat WhatsApp group chat analyzer')
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto = True, margin = 15)
    pdf.add_page()
    pdf.content(info_1)
    pdf.image('plots/top_10_active_days.png', x = 1, w = pdf.w - 3)
    pdf.content(info_2)
    pdf.image('plots/top_10_active_users.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/top_10_media_sharing.png', x = 1, w = pdf.w - 3)
    pdf.content(info_3)
    pdf.image('plots/active_hours.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/day_of_week.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/month_group.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/dh_heatmap.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/traffic.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/bar_leav_join.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/line_leav_join.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/leav_traffic.png', x = 1, w = pdf.w - 3)
    pdf.image('plots/engagement.png', x = 1, w = pdf.w - 3)
    github = 'https://github.com/shalomhalf/DaChat'
    pdf.cell(pdf.w - 10, 5, 'This analysis was created using DaChat WhatsApp group chat analyzer.  More information can be found here', link=github)


    pdf.output('results/{}_pdf.pdf'.format(df["group"][0]))

class App():
    def __init__(self):
        def open_text_file():
                # Specify the file types
            filetypes = (('text files', '*.txt'), ('All files', '*.*'))
            # Show the open file dialog by specifying the initial directory
            file_path = fd.askopenfilename(filetypes=filetypes, initialdir="D:/Downloads")
            if file_path:
                file_text.delete('1.0', tk.END)
                file_text.insert('1.0', file_path)
        def run_analysis():
            file = file_text.get('1.0', tk.END).rstrip()
            N = int(num_choice.get())
            category = str(category_choice.get())
            if file and N and category:
                raw_df = rawtodf(file, category)
                day_of_creation = None
                df , df_notification, day_of_creation = df_processing(raw_df, N)
                if os.path.isfile('results/fdf.csv')and os.path.isfile('fdf_notif.csv'):
                    df.to_csv('results/fdf.csv', mode='a', header=False, index=False)
                    df.to_csv('results/fdf_notif.csv', mode='a', header=False, index=False)
                else:
                    df.to_csv('results/fdf.csv', index=False)
                    df_notification.to_csv('results/fdf_notif.csv', index=False)
                date_group = None
                date_group = group_by_day(df , df_notification)
                plot_data(df ,date_group, raw_df, day_of_creation)
                tk.messagebox.showinfo(title='Congratulations!', message='Plots were saved in the "plots" folder \nPDF report was saved in the "results" folder \nThank you for using the DaChat')
            else:
                tk.messagebox.showwarning(title='Invalid Input', message='The user must enter all variables before running the analysis')

        self.root = tk.Tk()
        self.root.title('DaChat WhatsApp Analyzer')
        self.root.iconphoto(False, tk.PhotoImage(file='images/s_logo.png'))
        boldStyle = ttk.Style ()
        boldStyle.configure('Bold.TButton', font = ('Helvetica','14','bold'))
        
        #Frames Arrangement
        frame = tk.Frame(self.root)
        frame.pack()

        # Intro Frame
        intro_frame = tk.LabelFrame(frame, text='Intro')
        intro_frame.grid(row=0, column=0, sticky='news', padx=20, pady=10)

        intro_0_label = tk.Label(intro_frame, justify='left' ,text='Export the WhatsApp chat you like to analyze using the following steps: \n1. Open the WhatsApp chat \n2.Click the three vertical dots on top-right \n3. Click More \n4. Click Export Chat \n5. Click Without Media \n6. Save the generated .txt file where it is accessible ')
        intro_0_label.pack(padx=20, pady=10)

        # File_Frame
        file_frame = tk.LabelFrame(frame, text='Import Chat Data File')
        file_frame.grid(row=1, column=0, sticky='news', padx=20, pady=10)

        file_text = tk.Text(file_frame, height=1, width=40 , wrap="none")
        file_text.grid(row=0, column=0, padx=10 ,pady=5)

        file_button = ttk.Button(file_frame, text='Open File', command=open_text_file)
        file_button.grid(row=0, column=1, padx=10 ,pady=5)


        # Data Info Frame Arrangement
        data_info_frame = tk.LabelFrame(frame,text='Chat Data info')
        data_info_frame.grid(row=2, column=0, sticky='news', padx=20, pady=10)

        #top label
        data_info_label = tk.LabelFrame(data_info_frame, text='enter detels:')
        data_info_label.grid(row=0, column=0, padx=10 ,pady=5)

        #Data info labels

        num_label = tk.Label(data_info_frame, text='number of \n participants in group')
        num_label.grid(row=1 ,column=0, padx=10 ,pady=5)

        category_label=tk.Label(data_info_frame, text='group category')
        category_label.grid(row=1 ,column=1, padx=10 ,pady=5)

        #Data info choice
        num_choice = tk.Spinbox(data_info_frame, from_=0, to='infinity')
        num_choice.grid(row=2 , column=0, padx=10 ,pady=5)

        category_choice = tk.Entry(data_info_frame)
        category_choice.grid(row=2, column=1, padx=10 ,pady=5)
        
        # Save to Button


        # Submit Button Frame
        submit_button = ttk.Button(frame, text='Run Analysis', style='Bold.TButton', command=run_analysis)
        submit_button.grid(row=4 , column=0 ,sticky='news', padx=20, pady=20)

        self.root.mainloop()
        return

if __name__ == '__main__':
    App()