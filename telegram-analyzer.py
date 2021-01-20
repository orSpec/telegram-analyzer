import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from datetime import datetime
from tabulate import tabulate

def createChannel(file):
    with open(file, encoding="utf8") as f:
        d = json.load(f)

    channel = {}
    channel["name"] = d["name"]
    channel["id"] = d["id"]
    channel["type"] = d["type"]

    df = pd.DataFrame(d["messages"])
    df = df[["id", "type", "date", "text", "from", "from_id", "media_type", "edited"]]\
        .rename(columns={"from": "Username", "from_id": "UserID"})

    df = df[df["type"] == "message"]

    df["UserID"] = df["UserID"].astype(int)

    df["datetime"] = pd.to_datetime(df["date"])
    df["datetime_date"] = df["datetime"].dt.date
    df["datetime_year"] = df["datetime"].dt.year
    df["datetime_month"] = df["datetime"].dt.month
    df["datetime_hour"] = df["datetime"].dt.hour

    channel["messages"] = df

    return channel

def filterDataFrame(df, startDate = None, endDate = None):
    if startDate:
        df = df[df["datetime"] >= startDate]

    if endDate:
        df = df[df["datetime"] <= endDate]

    return df

def postingTimeChart(df):
    plt.figure(figsize=(10, 5))
    g = sns.countplot(x="datetime_hour", data=df, color="green", order=range(24))
    g.set_xlabel("Hour")
    g.set_title("Messages per hour")
    plt.savefig("postingTimeChart.png")

    return g

def messagesPerWeekday(df):
    plt.figure(figsize=(10, 5))
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    g = sns.countplot(x="datetime_weekday", data=df, color="green", order=order)
    g.set_xlabel("Weekday")
    g.set_title("Messages")
    plt.savefig("messagesPerWeekday.png")

    return g

def heatmapDayHours(df):
    data = df.groupby(["datetime_weekday", "datetime_hour"])["id"].count().reset_index()
    heat = data.pivot(index="datetime_weekday", columns="datetime_hour", values="id").reset_index().set_index("datetime_weekday")

    ## fill up missing hours
    hours = list(range(24))
    for x in hours:
        if x not in heat.columns:
            heat[x] = np.NaN

    # rearrange columns and transpose, then rearrange again
    heat = heat[range(24)]
    heat = heat.transpose()
    heat = heat[["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]

    plt.figure(figsize=(14, 12))
    g = sns.heatmap(heat,annot=True,fmt=".0f")
    plt.savefig("heatmap_Days_Hours.png")

    return g


def activityOverTime(df,users):
    plt.figure(figsize=(15, 5))

    if users:
        plot_data = df[df["UserID"].isin(users)].groupby(["UserID", "datetime_date"]).count()["id"]\
            .reset_index().rename(columns={"datetime_date": "Date", "id": "Messages"})
        g = sns.lineplot(x="Date", y="Messages", hue="UserID", data=plot_data, legend="full", palette="viridis")
    else:
        plot_data = df.groupby("datetime_date").count()["id"].reset_index()\
            .rename(columns={"datetime_date": "Date", "id": "Messages"})
        g = sns.lineplot(x="Date", y="Messages", data=plot_data)

    g.set_title("Activity (nr of messages) over time")
    plt.savefig("activityOverTime.png")

def getNMostActiveUser(df,n=None):
    mostActive = df.groupby("UserID").count()["id"].sort_values(ascending=False).reset_index().rename(columns={"id": "Messages"})

    if n:
        mostActive = mostActive.head(n)

    mostActive = mostActive.merge(df[["UserID", "Username"]], how="left").drop_duplicates()
    mostActive = mostActive[["Username", "UserID", "Messages"]]

    return mostActive

def mostActiveUsersPieChart(df, n=None):
    mostActiveUsers = getNMostActiveUser(df,n)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.pie(mostActiveUsers["Messages"], labels=mostActiveUsers["Username"], autopct="%1.1f%%", labeldistance=1.05, startangle=90)
    plt.axis('equal')
    plt.title("Message share per user", fontdict={"fontsize": 30})
    plt.savefig("mostActiveUsers.png")


def getStatistics(channel):

    df = channel["messages"]
    minDate = df["datetime_date"].min()
    maxDate = df["datetime_date"].max()
    daysInData = (maxDate - minDate).days + 1
    messages = len(df)
    meanNrOfMessages = round(df.groupby("datetime_date")["id"].count().mean(), 2)
    members = df["UserID"].nunique()

    dic = {"Channel": channel["name"], "Channel ID" : channel["id"], "Channel Type" : channel["type"],
           "Members": members, "Messages": messages, "First date": minDate,
           "Last date": maxDate, "Days in data": daysInData, "Mean # messages per day": meanNrOfMessages}

    return dic


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
    parser.add_argument("file", help="JSON file containing the telegram data")
    parser.add_argument("--start", type=datetime.fromisoformat, help="First date to consider, Format YYYY-MM-DD",
                        metavar="DATE")
    parser.add_argument("--end", type=datetime.fromisoformat, help="Last date to consider, Format YYYY-MM-DD",
                        metavar="DATE")
    parser.add_argument("-a", "--activity", default=[None], action="store", nargs="*", type=int, metavar = "UserID",
                        help="Create chart of activity over time of all users, pass one or multiple UserIDs to evaluate only these users")

    parser.add_argument("-dh", "--daysHours", action="store_true", help="Create heatmap of posting days vs. times")
    parser.add_argument("-ma", "--mostActive", type=isPositiveValue, help="Show n most active users: Need to pass n > 0",
                        metavar="nrOfUsers")
    parser.add_argument("-mac", "--mostActiveChart", type=isPositiveValue,
                        help="Create chart of n most active users:  Need to pass n > 0", metavar="nrOfUsers")

    parser.add_argument("-s", "--statistics", action="store_true",
                        help = "show statistics (#members, #messages, #mean nr of messages etc.")

    parser.add_argument("-t", "--time", action="store_true", help="Create chart of posting times")

    parser.add_argument("-w", "--weekday", action="store_true", help="Create chart of messages per weekday")



    args = parser.parse_args()

    channel = createChannel(args.file)

    df = channel["messages"]

    if args.start or args.end:
        df = filterDataFrame(df, startDate=args.start, endDate=args.end)

    if args.time:
        postingTimeChart(df)

    if args.daysHours:
        heatmapDayHours(df)

    if args.weekday:
        messagesPerWeekday(df)

    if args.activity != [None]:
        users = args.activity
        activityOverTime(df, users)

    if args.mostActive:
            nrUsers = args.mostActive
            mostActiveUsers = getNMostActiveUser(df, nrUsers)
            print(tabulate(mostActiveUsers, headers='keys', tablefmt='psql', showindex=False))

    if args.mostActiveChart:
        nrUsers = args.mostActiveChart
        mostActiveUsersPieChart(df, nrUsers)

    if args.statistics:
        stats = getStatistics(channel)
        print(tabulate(stats.items(), tablefmt='psql', showindex=False))


if __name__ == "__main__":
        main()