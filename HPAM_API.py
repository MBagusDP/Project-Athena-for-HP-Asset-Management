import pandas as pd
import dateutil.parser as parser
from datetime import datetime
import time
import openpyxl
import json
import requests
import gspread

# Connect to google service account
print("")
print("   Connecting to google sheet...")
# gc = gspread.service_account(filename="credential_keys/personal_credential.json")

# Open google sheet
# sh = gc.open("Your google sheet name here")

# Obtain all record from goodle sheet
print("   Getting all records from google sheet...")
gs_df = pd.DataFrame(sh.worksheet("Sheet1").get_all_records())

# Convert "created_at" to datetime
gs_df.created_at = gs_df.apply(lambda row: datetime.date(parser.parse(row["created_at"])), axis=1)
print("")
print("   Records found!")
print("   Latest date on google sheet:", gs_df.created_at.max())
print("   Updating data from", gs_df.created_at.max(), "to", datetime.date(datetime.now()))

# Prepare division DataFrame and empty DataFrame to be filled
# div = pd.read_excel("Excel/divisi.xlsx")
proms_df = pd.DataFrame()

# Request then convert data to DataFrame
for i in pd.period_range(gs_df.created_at.max(), datetime.date(datetime.now())):
    # Delay for 5 second to separate each request and preventing the PROMS API to be flooded by too many request
    print("     ", i)
    print("      Day:", i.strftime("%A"))
    time.sleep(10)
    print("   Requesting data from", str(i) + "...")
    div_empty = 0
    div_avail = 0
    for j in div.id:
        # header = {"param1": "param item"}
        # param = {"param2": j}
        # json_data = requests.post("Your API URL here", headers=header, data=param)
        if json_data.json()["success"] == True:
            div_avail = div_avail + 1
            # df = pd.json_normalize(json_data.json(), "message")
            # df["division"] = div.loc[div.id == j, "nama_divisi"].values[0]
            proms_df = pd.concat([proms_df, df])
        else:
            div_empty = div_empty + 1
    print("        ", div_avail, "number of divisions available for update")
    print("        ", div_empty, "number of divisions are not updated due to empty data")

# Renaming columns
proms_df = proms_df.rename(columns={"ttc": "time_to_completion", "cxy": "complexity", "rps": "related_parties"})

# Drop column named time_input
# Due to large empty data contains in this time_input column, I decided to discard the data.
# However, I might do an adjustment in the future
proms_df = proms_df.drop(columns=["time_input"])

# Remove noise
proms_df = proms_df.loc[(proms_df.time_to_completion != 0) &
                        (proms_df.complexity != 0) &
                        (proms_df.related_parties != 0) &
                        (proms_df.score != 0) &
                        (~proms_df.remarks.isna()) &
                        (~proms_df.score.isna())]

# Count words and create new column
proms_df["word_count"] = proms_df.remarks.str.split().str.len()

# Check whether the data has been updated or not
print("")
gs_df = pd.DataFrame(sh.sheet1.get_all_records())
tobe_updated = proms_df[~proms_df.created_at.isin(gs_df.created_at)]
proms_df = pd.concat([gs_df, tobe_updated])
print("   Available updates:", tobe_updated.shape[0])

if tobe_updated.shape[0] != 0:
    # Checking on rows before update
    print("")
    print("   Before update:")
    before = gs_df.shape[0]
    print("   Rows in google sheet:", before)

    # Upload dataframe to google sheet
    print("")
    print("   Updating...")
    sh.worksheet("Sheet1").update([proms_df.columns.values.tolist()] + proms_df.values.tolist())

    # Checking on rows after update
    gs_df = pd.DataFrame(sh.sheet1.get_all_records())
    print("")
    print("After update:")
    after = gs_df.shape[0]
    print("      Rows in google sheet:", after)
    print("      Updated rows:", after-before)

    # End report
    print("")
    print("Update Successful!")
    print("")
else:
    print("   Google sheet is up to date!")