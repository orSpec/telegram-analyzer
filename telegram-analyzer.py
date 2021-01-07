import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from datetime import datetime

def createDataFrame(file):
    with open(file, encoding="utf8") as f:
        d = json.load(f)

    df = pd.DataFrame(d["messages"])
    df = df[["id", "type", "date", "text", "from", "from_id", "media_type", "edited"]]

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


def main():

    parser = argparse.ArgumentParser(description="Analyse a Telegram JSON file. Simply read the file in and create insights.")
    parser.add_argument('file', help='JSON file containing the telegram data')
    parser.add_argument('--start', type=datetime.fromisoformat, help="First date to consider")
    parser.add_argument('--end', type=datetime.fromisoformat, help="Last date to consider")
    parser.add_argument('-t', '--time', action='store_true', help="Create and save chart of posting times")

    args = parser.parse_args()

    df = createDataFrame(args.file)

    if args.time:
        postingTimeChart(df)

    if args.start or args.end:
        df = filterDataFrame(df, startDate=args.start, endDate=args.end)

    if args.time:
        postingTimeChart(df)

if __name__ == "__main__":
        main()



