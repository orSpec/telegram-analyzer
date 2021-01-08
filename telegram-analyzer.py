import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from datetime import datetime
from tabulate import tabulate

def createDataFrame(file):
    with open(file, encoding="utf8") as f:
        d = json.load(f)

    df = pd.DataFrame(d["messages"])
    df = df[["id", "type", "date", "text", "from", "from_id", "media_type", "edited"]]
    df = df[df["type"] == "message"]

    df["from_id"] = df["from_id"].astype(int)

    df["datetime"] = pd.to_datetime(df["date"])
    df["datetime_date"] = df["datetime"].dt.date
    df["datetime_year"] = df["datetime"].dt.year
    df["datetime_month"] = df["datetime"].dt.month
    df["datetime_hour"] = df["datetime"].dt.hour

    return df

def filterDataFrame(df, startDate = None, endDate = None):
    if startDate:
        df = df[df["datetime"] >= startDate]

    if endDate:
        df = df[df["datetime"] <= endDate]

    return df

def postingTimeChart(df):
    plt.figure(figsize=(10, 5))
    g = sns.countplot(x="datetime_hour", data=df, color="green")
    g.set_xlabel("Hour")
    g.set_title("Messages per hour")
    plt.savefig("postingTimeChart.png")

    return g

def activityOverTime(df):
    plt.figure(figsize=(15, 5))

    plot_data = df.groupby("datetime_date").count()["id"].reset_index().rename(columns={"datetime_date" : "Date", "id" : "Messages"})
    g = sns.lineplot(x="Date", y="Messages", data=plot_data)
    g.set_title("Activity (nr of messages) over time")
    plt.savefig("activityOverTime.png")

def getNMostActiveUser(df,n=None):
    mostActive = df.groupby("from_id").count()["id"].sort_values(ascending=False).reset_index().rename(columns={"id" : "Messages"})

    if n:
        mostActive = mostActive.head(n)

    mostActive = mostActive.merge(df[["from_id", "from"]], how="left").drop_duplicates().rename(columns={"from": "Username", "from_id" : "UserID"})
    mostActive = mostActive[["Username", "UserID", "Messages"]]

    return mostActive

def mostActiveUsersPieChart(df, n=None):
    mostActiveUsers = getNMostActiveUser(df,n)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.pie(mostActiveUsers["Messages"], labels=mostActiveUsers["Username"], autopct="%1.1f%%", labeldistance=1.05, startangle=90)
    plt.axis('equal')
    plt.title("Message share per user", fontdict={"fontsize": 30})
    plt.savefig("mostActiveUsers.png")


def isPositiveValue(input):
    try:
        value = int(input)
    except ValueError:
        raise argparse.ArgumentTypeError("invalid value: must be a positive int")

    if value <= 0:
        raise argparse.ArgumentTypeError("invalid value: must be a positive int")

    return value

def main():

    parser = argparse.ArgumentParser(description="Analyse a Telegram JSON file. Simply read the file in and create insights.")
    parser.add_argument('file', help='JSON file containing the telegram data')
    parser.add_argument('--start', type=datetime.fromisoformat, help="First date to consider")
    parser.add_argument('--end', type=datetime.fromisoformat, help="Last date to consider")
    parser.add_argument('-a', '--activity', action='store_true', help="Create chart of activity over time")
    parser.add_argument('-t', '--time', action='store_true', help="Create chart of posting times")
    parser.add_argument('-ma', '--mostActive', type=isPositiveValue, help='Show n most active users: Need to pass n > 0')
    parser.add_argument('-mac', '--mostActiveChart', type=isPositiveValue, help='Create chart of n most active users:  Need to pass n > 0')

    args = parser.parse_args()

    df = createDataFrame(args.file)

    if args.start or args.end:
        df = filterDataFrame(df, startDate=args.start, endDate=args.end)

    if args.time:
        postingTimeChart(df)

    if args.activity:
        activityOverTime(df)

    if args.mostActive:
            nrUsers = args.mostActive
            mostActiveUsers = getNMostActiveUser(df, nrUsers)
            print(tabulate(mostActiveUsers, headers='keys', tablefmt='psql', showindex=False))

    if args.mostActiveChart:
        nrUsers = args.mostActiveChart
        mostActiveUsersPieChart(df, nrUsers)


if __name__ == "__main__":
        main()



