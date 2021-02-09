from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from datetime import timedelta, datetime

# create engine to hawaii.sqlite
engine = create_engine("sqlite:///hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# View all of the classes that automap found
Base.classes.keys()
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#-----------
#Exploratory Precipitation Analysis

# Find the most recent date in the data set.
recentDate = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
#recentDate

# Design a query to retrieve the last 12 months of precipitation data and plot the results. 
# Starting from the most recent data point in the database.
## 最近資料的站點
# recentStation = session.query(Measurement).order_by(Measurement.date.desc()).first().station
## 最近資料的日期
recentDate = datetime.strptime(recentDate.date, "%Y-%m-%d")
# Calculate the date one year from the last date in data set.  ## 最近資料的日期前一年
oneYearAgoDate = recentDate - dt.timedelta(days = 365)

# Perform a query to retrieve the data and precipitation scores
query = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= oneYearAgoDate).all()

# Save the query results as a Pandas DataFrame and set the index to the date column
df = pd.DataFrame(query).set_index('date')

# Sort the dataframe by date
df = df.sort_index()
# Use Pandas Plotting with Matplotlib to plot the data
df.plot()
plt.show()


# Use Pandas to calcualte the summary statistics for the precipitation data
df.describe()

#---------------------

#Exploratory Station Analysis

# Design a query to calculate the total number stations in the dataset
totalNumberStations = session.query(Measurement).group_by(Measurement.station).count()
print(totalNumberStations)
#也可 session.query(func.count(Station.station)).all()  



# Design a query to find the most active stations (i.e. what stations have the most rows?)
stationGroupQuery = session.query(Measurement.station, func.count(Measurement.id).label('count')).group_by(Measurement.station)

mostActiveStations = stationGroupQuery.order_by(func.count(Measurement.id).desc()).first()
print('most active stations:', mostActiveStations.station)
# List the stations and the counts in descending order.
for row in stationGroupQuery.order_by(func.count(Measurement.id).desc()).all():
    print(row.station, row.count)

#或許可以?
# join = session.query(Measurement, Station).filter(Measurement.station == Station.station).all()
#most_active = session.query(join).group_by(join.station).order_by(join.station.desc()).first()
#station_active_count = session.query(join).group_by(join.station).order_by(join.station.desc()).all()



# Using the most active station id from the previous query, calculate the lowest, highest, and average temperature.
lowest = session.query(Measurement).filter(Measurement.station == mostActiveStations.station).order_by(Measurement.tobs).first().tobs
print('lowest:', lowest)
highest = session.query(Measurement).filter(Measurement.station == mostActiveStations.station).order_by(Measurement.tobs.desc()).first().tobs
print('highest:', highest)
average = session.query(func.avg(Measurement.tobs).label('average')).filter(Measurement.station == mostActiveStations.station).first().average
print('average:', average)

#也可以
# sel[func.max(Measurement.tobs),func.min(Measurement.tobs), func.avg(Measurement.tobs)]
# tem_data = session.query(*sel).filter(Measurement.station == "USC00519281").all()



# Using the most active station id
## mostActiveStations.station
# Query the last 12 months of temperature observation data for this station and plot the results as a histogram
final =session.query(Measurement.tobs).filter(Measurement.date >= oneYearAgoDate).filter(Measurement.station == "USC00519281").all()

df = pd.DataFrame(final)
df.plot.hist(bins = 12)
plt.show()


session.close()
#-------------------------------------------

# 用前面求得的資料作出flask API
# / 
# Home page.主頁
# List all routes that are available.列出所有available的routes

from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def Home():
    
    return(
        f"Welcome to the Climate API!<br>"
        f"available routes<br>"
        f"/api/v1.0/precipitation<br>"
        f"/api/v1.0/stations<br>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/start and /api/v1.0/start/end")



# /api/v1.0/precipitation 
# Convert the query results to a dictionary using date as the key and prcp as the value.
# 把資料轉換成dictionary - date as key & prcp as value
# Return the JSON representation of your dictionary.不知道這是甚麼意思

@app.route("/api/v1.0/precipitation")
def precipitation():
    
    session = Session(engine)
    results = session.query(Measurement.date, Measurement.prcp).all()
    session.close()

    precipitation_list = []
    for date, prcp in results:    
        dictionary = {}
        dictionary[date] = prcp
      
        precipitation_list.append(dictionary)


    return jsonify(precipitation_list)





# /api/v1.0/stations
# Return a JSON list of stations from the dataset

@app.route("/api/v1.0/stations")
def stations():
    
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()

    station_list = list(np.ravel(results))

    return jsonify(station_list)





# /api/v1.0/tobs
# Query the dates and temperature observations of the most active station for the last year of data.
# 求出過去的一年,最多資料筆數的天氣站的dates & temperature
# Return a JSON list of temperature observations (TOBS) for the previous year.


@app.route("/api/v1.0/tobs")
def tobs():
    
    session = Session(engine)
    recentDate = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    recentDate = datetime.strptime(recentDate.date, "%Y-%m-%d")
    oneYearAgoDate = recentDate - dt.timedelta(days = 365)

    results = session.query(Measurement.tobs).filter(Measurement.station == "USC00519281").filter(Measurement.date >= oneYearAgoDate).all()
    session.close()

    tobs_data = list(np.ravel(results))

    return jsonify(tobs_data)






# /api/v1.0/<start> and /api/v1.0/<start>/<end>
# Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
# When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
# When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.



# @app.route("/api/v1.0/<start>")
# def yo(start):
#     startDate = datetime.strptime(startdate, "%Y-%m-%d")
    
#     session = Session(engine)
#     results = session.query(func.max(Measurement.tobs), func.min(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date >= start).all()
#     session.close()

#     return jsonify(results)




@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def date(start, end = None):
    startDate = datetime.strptime(start, "%Y-%m-%d")
    endDate = ""
    results = []
    session = Session(engine)

    if end != None:
        endDate = datetime.strptime(end, "%Y-%m-%d")
        count = session.query(Measurement).filter(Measurement.date >= startDate).filter(Measurement.date <= endDate).count()

        if count == 0:
            return jsonify({"erro": "data can't find"}), 404
        
        results = session.query(func.max(Measurement.tobs), func.min(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date >= startDate).filter(Measurement.date <= endDate).all()
    else:
        count = session.query(Measurement).filter(Measurement.date >= startDate).count()

        if count == 0:
            return jsonify({"erro": "data can't find"}), 404

        results = session.query(func.max(Measurement.tobs), func.min(Measurement.tobs),func.avg(Measurement.tobs)).filter(Measurement.date >= startDate).all()

    session.close()

    return jsonify(results)






if __name__ == "__main__":
    app.run(debug=True)
