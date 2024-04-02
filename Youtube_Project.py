from googleapiclient.discovery import build
import pymongo
import mysql.connector
import pandas as pd
import streamlit as st


#API key connection

def Api_connect():
    Api_Id="AIzaSyC7uiKclPszYlB29VyJHjz-jC8rOSHDDIs"

    api_service_name="youtube"
    api_version="v3"

    youtube=build(api_service_name,api_version,developerKey=Api_Id)

    return youtube

youtube=Api_connect()
#get channels information
def get_channel_info(channel_id):
    request=youtube.channels().list(
                    part="snippet,ContentDetails,statistics",
                    id=channel_id
    )
    response=request.execute()

    for i in response['items']:
        data=dict(Channel_Name=i["snippet"]["title"],
                Channel_Id=i["id"],
                Subscribers=i['statistics']['subscriberCount'],
                Views=i["statistics"]["viewCount"],
                Total_Videos=i["statistics"]["videoCount"],
                Channel_Description=i["snippet"]["description"],
                Playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
    return data


#get video ids
def get_videos_ids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id=channel_id,
                                    part='contentDetails').execute()
    Playlist_Id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token=None

    while True:
        response1=youtube.playlistItems().list(
                                            part='snippet',
                                            playlistId=Playlist_Id,
                                            maxResults=50,
                                            pageToken=next_page_token).execute()
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token=response1.get('nextPageToken')

        if next_page_token is None:
            break
    return video_ids


#get video information
def get_video_info(video_ids):
    video_data=[]
    for video_id in video_ids:
        request=youtube.videos().list(
            part="snippet,ContentDetails,statistics",
            id=video_id
        )
        response=request.execute()

        for item in response["items"]:
            data=dict(Channel_Name=item['snippet']['channelTitle'],
                    Channel_Id=item['snippet']['channelId'],
                    Video_Id=item['id'],
                    Title=item['snippet']['title'],
                    Tags=item['snippet'].get('tags'),
                    Thumbnail=item['snippet']['thumbnails']['default']['url'],
                    Description=item['snippet'].get('description'),
                    Published_Date=item['snippet']['publishedAt'],
                    Duration=item['contentDetails']['duration'],
                    Views=item['statistics'].get('viewCount'),
                    Likes=item['statistics'].get('likeCount'),
                    Comments=item['statistics'].get('commentCount'),
                    Favorite_Count=item['statistics']['favoriteCount'],
                    Definition=item['contentDetails']['definition'],
                    Caption_Status=item['contentDetails']['caption']
                    )
            video_data.append(data)    
    return video_data


#get comment information
def get_comment_info(video_ids):
    Comment_data=[]
    try:
        for video_id in video_ids:
            request=youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50
            )
            response=request.execute()

            for item in response['items']:
                data=dict(Comment_Id=item['snippet']['topLevelComment']['id'],
                        Video_Id=item['snippet']['topLevelComment']['snippet']['videoId'],
                        Comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        Comment_Published=item['snippet']['topLevelComment']['snippet']['publishedAt'])
                
                Comment_data.append(data)
                
    except:
        pass
    return Comment_data


#get_playlist_details

def get_playlist_details(channel_id):
        next_page_token=None
        All_data=[]
        while True:
                request=youtube.playlists().list(
                        part='snippet,contentDetails',
                        channelId=channel_id,
                        maxResults=50,
                        pageToken=next_page_token
                )
                response=request.execute()

                for item in response['items']:
                        data=dict(Playlist_Id=item['id'],
                                Title=item['snippet']['title'],
                                Channel_Id=item['snippet']['channelId'],
                                Channel_Name=item['snippet']['channelTitle'],
                                PublishedAt=item['snippet']['publishedAt'],
                                Video_Count=item['contentDetails']['itemCount'])
                        All_data.append(data)

                next_page_token=response.get('nextPageToken')
                if next_page_token is None:
                        break
        return All_data


#upload to mongoDB

client=pymongo.MongoClient("mongodb://localhost:27017/")
db = client['Sample_Youtube_Data']

def channel_details(channel_id):
    ch_details=get_channel_info(channel_id)
    pl_details=get_playlist_details(channel_id)
    vi_ids=get_videos_ids(channel_id)
    vi_details=get_video_info(vi_ids)
    com_details=get_comment_info(vi_ids)

    coll1=db["channel_details"]
    coll1.insert_one({"channel_information":ch_details,"playlist_information":pl_details,
                      "video_information":vi_details,"comment_information":com_details})
    
    return "upload completed successfully"

#get channels tables

def channels_table():
    config ={
        'user':'root', 'password':'Roman@9804r',
        'host':'127.0.0.1','database':'Sample_Youtube_Data'
    }

    connection =mysql.connector.connect(**config)
    cursor = connection.cursor()

    drop_query="""drop table if exists channels"""
    cursor.execute(drop_query)
    connection.commit

    try:
        create_query="""create table if not exists channels(Channel_Name varchar(100),
                                                            Channel_Id varchar(80) primary key,
                                                            Subscribers int,
                                                            Views int,
                                                            Total_Videos int,
                                                            Channel_Description text,
                                                            Playlist_Id varchar(80))"""
        
        cursor.execute(create_query)
        connection.commit()


    except:
        print("channels table already created") 

    ch_list=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=pd.DataFrame(ch_list) 


    for index,row in df.iterrows():
        insert_query1="""insert into channels(Channel_Name,
                                            Channel_Id,
                                            Subscribers,
                                            Views,
                                            Total_Videos,
                                            Channel_Description,
                                            Playlist_Id)
                                            
                                            values(%s,%s,%s,%s,%s,%s,%s)"""
        
        values=(row['Channel_Name'],
                row['Channel_Id'],
                row['Subscribers'],
                row['Views'],
                row['Total_Videos'], 
                row['Channel_Description'],
                row['Playlist_Id'])
        
        try:
            cursor.execute(insert_query1,values)
            connection.commit()

        except:
            print("channels values are already created")


#Get playlist table
            
def playlist_table():
    config ={
    'user':'root', 'password':'Roman@9804r',
    'host':'127.0.0.1','database':'Sample_Youtube_Data'
    }

    connection =mysql.connector.connect(**config)
    cursor = connection.cursor()

    drop_query="""drop table if exists playlists"""
    cursor.execute(drop_query)
    connection.commit

    create_query='''create table if not exists playlists(Playlist_Id varchar(100),
                                                        Title varchar(100),
                                                        Channel_Id varchar(100),
                                                        Channel_Name varchar(100),
                                                        PublishedAt varchar(100),
                                                        Video_Count int
                                                        )'''

    cursor.execute(create_query)
    connection.commit()

    pl_list=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])): 
            pl_list.append(pl_data["playlist_information"][i])
    df1=pd.DataFrame(pl_list)

    for index,row in df1.iterrows():
            insert_query='''insert into playlists(Playlist_Id,
                                            Title,
                                            Channel_Id,
                                            Channel_Name,
                                            PublishedAt,
                                            Video_Count
                                            )
                                            
                                            values(%s,%s,%s,%s,%s,%s)'''
        
            values=(row['Playlist_Id'],
                row['Title'],
                row['Channel_Id'],
                row['Channel_Name'],
                row['PublishedAt'],
                row['Video_Count']
                )

        
            cursor.execute(insert_query,values)
            connection.commit()

#get videos table
            
def videos_table():
    config ={
    'user':'root', 'password':'Roman@9804r',
    'host':'127.0.0.1','database':'Sample_Youtube_Data'
    }

    connection =mysql.connector.connect(**config)
    cursor = connection.cursor()

    drop_query="""drop table if exists videos"""
    cursor.execute(drop_query)
    connection.commit

    create_query='''create table if not exists videos(Channel_Name varchar(100),
                                                    Channel_Id varchar(100),
                                                    Video_Id varchar(50),
                                                    Title varchar(150),
                                                    Thumbnail varchar(200),
                                                    Description text,
                                                    Published_Date varchar(100),
                                                    Duration varchar(100),
                                                    Views int,
                                                    Likes int,
                                                    Comments int,
                                                    Favorite_Count int,
                                                    Definition varchar(10),
                                                    Caption_Status varchar(50)
                                                        )'''

    cursor.execute(create_query)
    connection.commit()


    vi_list=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])): 
            vi_list.append(vi_data["video_information"][i])
    df2=pd.DataFrame(vi_list) 


    for index,row in df2.iterrows():
            insert_query='''INSERT INTO videos(Channel_Name,
                                                    Channel_Id,
                                                    Video_Id,
                                                    Title,
                                                    Thumbnail,
                                                    Description,
                                                    Published_Date,
                                                    Duration,
                                                    Views,
                                                    Likes,
                                                    Comments,
                                                    Favorite_Count,
                                                    Definition,
                                                    Caption_Status
                                                    )
                                                
                                                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            values=(row['Channel_Name'],
                            row['Channel_Id'],
                            row['Video_Id'],
                            row['Title'],
                            row['Thumbnail'][0:50],
                            row['Description'],
                            row['Published_Date'],
                            row['Duration'],
                            row['Views'],
                            row['Likes'],
                            row['Comments'],
                            row['Favorite_Count'],
                            row['Definition'],
                            row['Caption_Status']
                            )
            

            cursor.execute(insert_query,values)
            connection.commit()

#get comments table
def comments_table():
        config ={
        'user':'root', 'password':'Roman@9804r',
        'host':'127.0.0.1','database':'Sample_Youtube_Data'
        }

        connection =mysql.connector.connect(**config)
        cursor = connection.cursor()
        create_query='''create table if not exists comments(Comment_Id varchar(100),
                                                        Video_Id varchar(50),
                                                        Comment_Text text,
                                                        Comment_Author varchar(150),
                                                        Comment_Published varchar(100)
                                                        )'''

        cursor.execute(create_query)
        connection.commit()

        com_list=[]
        db=client["Sample_Youtube_Data"]
        coll1=db["channel_details"]
        for com_data in coll1.find({},{"_id":0,"comment_information":1}):
           for i in range(len(com_data["comment_information"])): 
               com_list.append(com_data["comment_information"][i])
        df3=pd.DataFrame(com_list) 

        for index,row in df3.iterrows():
                insert_query='''insert into comments(Comment_Id,
                                                        Video_Id,
                                                        Comment_Text,
                                                        Comment_Author,
                                                        Comment_Published
                                                )
                                                
                                                values(%s,%s,%s,%s,%s)'''
                
                
                values=(row['Comment_Id'],
                        row['Video_Id'],
                        row['Comment_Text'],
                        row['Comment_Author'],
                        row['Comment_Published']
                        )

                
                cursor.execute(insert_query,values)
                connection.commit()


#Fetch the all tables
def tables():
           channels_table()
           playlist_table()
           videos_table()
           comments_table()

           return "All tables created successfully"


def view_channels_table():
    ch_list=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=st.dataframe(ch_list) 

    return df

def view_playlists_table():
    pl_list=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
            for i in range(len(pl_data["playlist_information"])): 
                pl_list.append(pl_data["playlist_information"][i])
    df1=st.dataframe(pl_list)

    return df1

def view_videos_tables():
    vi_list=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])): 
            vi_list.append(vi_data["video_information"][i])
    df2=st.dataframe(vi_list)

    return df2

def view_comments_table(): 
    com_list=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])): 
            com_list.append(com_data["comment_information"][i])
    df3=st.dataframe(com_list) 

    return df3

def view_comments_table(): 
    com_list=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])): 
            com_list.append(com_data["comment_information"][i])
    df3=st.dataframe(com_list) 

    return df3

#streamlit part

with st.sidebar:
    st.title(":green[YOUTUBE DATA HAVERSTING AND WAREHOUSING]")
    st.header("HOME")

channel_id=st.text_input("Enter the Youtube channel ID below")

if st.button("collect and store data"):
    ch_ids=[]
    db=client["Sample_Youtube_Data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_ids.append(ch_data["channel_information"]["Channel_Id"])

    if channel_id in ch_ids:
        st.success("Channel Details of the given channel id already exists")

    else:
        insert=channel_details(channel_id)
        st.success(insert)

#New code       
if st.button("Migrate to Sql"):
    Table=tables()
    st.success(Table)

show_table=st.radio("SELECT THE TABLE FOR VIEW",("CHANNELS","PLAYLISTS","VIDEOS","COMMENTS"))

if show_table=="CHANNELS":
    view_channels_table()

elif show_table=="PLAYLISTS":
    view_playlists_table()

elif show_table=="VIDEOS":
    view_videos_tables()

elif show_table=="COMMENTS":
    view_comments_table()

#SQL Connection

config ={
    'user':'root', 'password':'Roman@9804r',
    'host':'127.0.0.1','database':'Sample_Youtube_Data'
}

connection =mysql.connector.connect(**config)
cursor = connection.cursor()

question=st.selectbox("Select your question",("1. What are the names of all the videos and their corresponding channels?",
                                              "2. Which channels have the most number of videos, and how many videos do they have?",   
                                              "3. What are the top 10 most viewed videos and their respective channels?",
                                              "4. How many comments were made on each video, and what are their  corresponding video names?",
                                              "5. Which videos have the highest number of likes, and what are their corresponding channel names?", 
                                              "6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?",
                                              "7. What is the total number of views for each channel, and what are their corresponding channel names?", 
                                              "8. What are the names of all the channels that have published videos in the year 2022?",
                                              "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                                              "10. Which videos have the highest number of comments, and what are their corresponding channel names?")) 


if question=="1. What are the names of all the videos and their corresponding channels?":
    query1='''select title as videos,channel_name as channelname from videos'''
    cursor.execute(query1)
    t1=cursor.fetchall()
    df=pd.DataFrame(t1,columns=["video title","channel name"])
    st.write(df)

elif question=="2. Which channels have the most number of videos, and how many videos do they have?":
    query2='''select channel_name as channelname,total_videos as no_videos from channels 
                order by total_videos desc'''
    cursor.execute(query2)
    t2=cursor.fetchall()
    df2=pd.DataFrame(t2,columns=["channel name","No of videos"])
    st.write(df2)

elif question=="3. What are the top 10 most viewed videos and their respective channels?":
    query3='''select views as views,channel_name as channelname,title as videotitle from videos 
                where views is not null order by views desc limit 10'''
    cursor.execute(query3)
    t3=cursor.fetchall()
    df3=pd.DataFrame(t3,columns=["views","channel name","videotitle"])
    st.write(df3)

elif question=="4. How many comments were made on each video, and what are their  corresponding video names?":
    query4='''select comments as no_comments,title as videotitle from videos where comments is not null'''
    cursor.execute(query4)
    t4=cursor.fetchall()
    df4=pd.DataFrame(t4,columns=["no of comments","videotitle"])
    st.write(df4)

elif question=="5. Which videos have the highest number of likes, and what are their corresponding channel names?":
    query5='''select title as videotitle,channel_name as channelname,likes as likecount
                from videos where likes is not null order by likes desc'''
    cursor.execute(query5)
    t5=cursor.fetchall()
    df5=pd.DataFrame(t5,columns=["videotitle","channelname","likecount"])
    st.write(df5)

elif question=="6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?":
    query6='''select likes as likecount,title as videotitle from videos'''
    cursor.execute(query6)
    t6=cursor.fetchall()
    df6=pd.DataFrame(t6,columns=["likecount","videotitle"])
    st.write(df6)

elif question=="7. What is the total number of views for each channel, and what are their corresponding channel names?":
    query7='''select channel_name as channelname ,views as totalviews from channels'''
    cursor.execute(query7)
    t7=cursor.fetchall()
    df7=pd.DataFrame(t7,columns=["channel name","totalviews"])
    st.write(df7)

elif question=="8. What are the names of all the channels that have published videos in the year 2022?":
    query8='''select title as video_title,published_date as videorelease,channel_name as channelname from videos
                where extract(year from published_date)=2022'''
    cursor.execute(query8)
    t8=cursor.fetchall()
    df8=pd.DataFrame(t8,columns=["videotitle","published_date","channelname"])
    st.write(df8)

elif question=="9. What is the average duration of all videos in each channel, and what are their corresponding channel names?":
    query9='''select channel_name as channelname,AVG(duration) as averageduration from videos group by channel_name'''
    cursor.execute(query9)
    t9=cursor.fetchall()
    df9=pd.DataFrame(t9,columns=["channelname","averageduration"])

    T9=[]
    for index,row in df9.iterrows():
        channel_title=row["channelname"]
        average_duration=row["averageduration"]
        average_duration_str=str(average_duration)
        T9.append(dict(channeltitle=channel_title,avgduration=average_duration_str))
    df1=pd.DataFrame(T9)
    st.write(df1)

elif question=="10. Which videos have the highest number of comments, and what are their corresponding channel names?":
    query10='''select title as videotitle, channel_name as channelname,comments as comments from videos where comments is
                not null order by comments desc'''
    cursor.execute(query10)
    t10=cursor.fetchall()
    df10=pd.DataFrame(t10,columns=["video title","channel name","comments"])
    st.write(df10)



