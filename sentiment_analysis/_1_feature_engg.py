import os
import pandas as pd
from pathlib import Path

PROJECT_PATH = Path().absolute().parent
filter_values = ["Highest_Rating", "Lowest_Rating", "Newest"]
reviews_df = pd.DataFrame()
for FILTER_NAME in filter_values:
    if(reviews_df.empty):
        reviews_df = pd.read_csv(os.path.join(PROJECT_PATH, f"bestbuy_reviews_{FILTER_NAME}.csv"))
    else:
        reviews_df = pd.concat([reviews_df, pd.read_csv(os.path.join(PROJECT_PATH, f"bestbuy_reviews_{FILTER_NAME}.csv"))])


## Drop duplicate IDs from the concatenated dataset
reviews_df = reviews_df.drop_duplicates(subset=["review_ID"])   
print(reviews_df.shape)
reviews_df.to_csv(os.path.join(PROJECT_PATH,"data/All_reviews.csv"), index=False)
