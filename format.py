import pandas as pd
import json

# Path to your Excel file
excel_path = r"C:\Users\jumpi\Downloads\LinkedIn_API_Format.xlsx"
df = pd.read_excel(excel_path)

profiles = {"elements": []}

for idx, row in df.iterrows():

    # Read values exactly matching your Excel column names
    profile_id = str(row.get("id", ""))  
    urn = row.get("urn", "")

    # Safely handle profile picture URL
    profile_pic_url = row.get("profilepictureurl")
    if pd.isna(profile_pic_url) or not isinstance(profile_pic_url, str):
        profile_pic_url = None

    profile = {
        "id": profile_id,
        "urn": urn,
        "localizedFirstName": str(row.get("localisedfirstName", "")),
        "localizedLastName": str(row.get("localisedLastName", "")),
        "localizedHeadline": str(row.get("localizedHeadline", "")),
        "publicProfileUrl": str(row.get("linkedinUrl", "")),
        "profilePicture": {
            "displayImage~": {
                "elements": [
                    {
                        "identifiers": [
                            {
                                "identifier": profile_pic_url
                            }
                        ]
                    }
                ]
            }
        }
    }

    profiles["elements"].append(profile)

# Save JSON output
json_path = "Backend/profiles.json"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(profiles, f, indent=2)

print(f"✅ JSON saved to {json_path}")
