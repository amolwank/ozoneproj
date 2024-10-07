import csv
from opensearchpy import OpenSearch

# Configuration for OpenSearch
hostname = 'vpc-in-ccaas-saaofdmzrqgseigfzxfna3dfwu.ap-south-1.es.amazonaws.com'
port = 443
username = 'log'
password = 'Ozone#123'

# Create an OpenSearch client
opensearch = OpenSearch(
    [{'host': hostname, 'port': port}],
    http_auth=(username, password),
    use_ssl=True,
    verify_certs=True
)

# Index name and aggregation query
index_name = 'in_ccaas_prod_analitics-2024.05.*'

query = {
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "time": {
              "gte": "2024/05/08 00:00:00",
              "lte": "2024/05/08 23:59:59"
            }
          }
        }
      ]
    }
  },
  "size": 0,
  "aggs": {
    "group_by_username": {
      "terms": {
        "field": "username.keyword",
        "include": {
          "partition": 0, 
          "num_partitions": 10
        },
        "size": 1000 
      },
      "aggs": {
        "group_by_hourly_time": {
          "date_histogram": {
            "field": "time",
            "interval": "hour",
            "format": "yyyy-MM-dd HH:mm:ss"
          },
          "aggs": {
            "group_by_did": {
              "terms": {
                "field": "portsutilization.did.keyword",
                "size": 1000 
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
      }
    }
  }
}


# Execute the search query
search_results = opensearch.search(index=index_name, body=query)

# File path for CSV output
csv_file_path = "Files//csvlocation/portutilization/portutilization.csv"

# Write results to CSV
with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["username","time", "did", "max_count", "sum_of_max_counts"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for username_bucket in search_results['aggregations']['group_by_username']['buckets']:
        username = username_bucket['key']
        for hourly_bucket in username_bucket['group_by_hourly_time']['buckets']:
            sum_of_max_counts = hourly_bucket['sum_of_max_counts']['value']
            time = hourly_bucket['key_as_string']  # This captures the time interval
            if isinstance(sum_of_max_counts, float) and sum_of_max_counts.is_integer():
                    sum_of_max_counts = int(sum_of_max_counts)  # Convert to integer if it's a whole number 
            for did_bucket in hourly_bucket['group_by_did']['buckets']:
                did = did_bucket['key']
                max_count = did_bucket['max_count']['value']
                if isinstance(max_count, float) and max_count.is_integer():
                    max_count = int(max_count)  # Convert to integer if it's a whole number
                writer.writerow({
                    "username": username,
                     "time": time,
                    "did": did,
                    "max_count": max_count,
                    "sum_of_max_counts": sum_of_max_counts
                })

print(f"CSV file with search results saved: {csv_file_path}")
