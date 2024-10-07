import csv
import os
from datetime import datetime
from datetime import datetime, timedelta
from opensearchpy import OpenSearch


# Calculate yesterday's date
yesterday = datetime.now() - timedelta(days=1)
yesterday_str = yesterday.strftime("%Y/%m/%d")  # Format as 'YYYY/MM/DD'
index_date = yesterday.strftime("%Y.%m.%d")  # Format for index

# Configuration for OpenSearch
hostname = 'vpc-pre-prod-mkppvuvrdkprvitdnajaesjgxm.ap-south-1.es.amazonaws.com'
port = 443
username = 'ccaas-preprod-admin'
password = 'Ozone#123'

def convert_if_integer(value):
    """Converts a float to an integer if it is a whole number."""
    return int(value) if isinstance(value, float) and value.is_integer() else value


# Create an OpenSearch client
opensearch = OpenSearch(
    [{'host': hostname, 'port': port}],
    http_auth=(username, password),
    use_ssl=True,
    verify_certs=True
)

# Index name
#index_name = 'in_ccaas_prod_analitics-2024.05.18'
# Index name with dynamic date
index_name = f'in_ccaas_prod_analitics-{index_date}'

# Initial query to fetch unique usernames
username_query = {
    "size": 0,
    "aggs": {
        "unique_usernames": {
            "terms": {
                "field": "username.keyword",
                "size": 10000
            }
        }
    }
}

# Fetch unique usernames
usernames_response = opensearch.search(index=index_name, body=username_query)
usernames = [bucket['key'] for bucket in usernames_response['aggregations']['unique_usernames']['buckets']]

# Define the directory path where you want to create the file
directory_path = "Files/csvlocation_elk/portutilization/"
os.makedirs(directory_path, exist_ok=True)  # Ensure directory exists
csv_file_path = os.path.join(directory_path, "portutilization.csv")
# File path for CSV output
#csv_file_path = "Files/user_data_detailed.csv"

# Open CSV file to write the data
with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
    fieldnames = ["username", "time_interval", "did", "max_count", "sum_of_max_counts", "user", "db", "table", "dt"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    #writer.writeheader()

    # Perform detailed query for each username
    for username in usernames:
        print(username)
        detailed_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"username.keyword": username}},
                        {"range": {"time": {"gte": f"{yesterday_str} 00:00:00", "lte": f"{yesterday_str} 23:59:59"}}}
                    ]
                }
            },
            "aggs": {
                "group_by_hourly_time": {
                    "date_histogram": {
                        "field": "time",
                        "calendar_interval": "hour",
                        "format": "yyyy-MM-dd HH:mm:ss"
                    },
                    "aggs": {
                        "group_by_did": {
                            "terms": {
                                "field": "portsutilization.did.keyword",
                                "size": 50000
                            },
                            "aggs": {
                                "max_count": {
                                    "max": {
                                        "field": "portsutilization.count"
                                    }
                                }
                            }
                        },
                        "sum_of_max_counts": {
                            "sum_bucket": {
                                "buckets_path": "group_by_did>max_count"
                            }
                        }
                    }
                }
            },
            "size": 0
        }

        # Execute detailed query
        response = opensearch.search(index=index_name, body=detailed_query)

        # Process aggregation results and write to CSV
        for hourly_bucket in response['aggregations']['group_by_hourly_time']['buckets']:
            time_interval = hourly_bucket['key_as_string']
            dt = datetime.strptime(time_interval, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            for did_bucket in hourly_bucket['group_by_did']['buckets']:
                did = did_bucket['key']
                max_count = did_bucket['max_count']['value']
                sum_of_max_counts = hourly_bucket['sum_of_max_counts']['value']
                writer.writerow({
                    "username": username,
                    "time_interval": time_interval,
                    "did": did,
                    "max_count": convert_if_integer(max_count),
                    "sum_of_max_counts": convert_if_integer(sum_of_max_counts),
                    "user": "usr_ozone",
                    "db": "default",
                    "table": "portutilization",
                    "dt": dt
                })

print(f"Data for all users saved to {csv_file_path}")
