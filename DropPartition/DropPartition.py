import sys
import os
import datetime
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
main_parent = os.path.dirname(parent)
sys.path.append(main_parent)
import job_runner

current_time = datetime.datetime.now()
current_time_minus_1 =  current_time - datetime.timedelta(days=1)
current_day_minus_1 = "%04d-%02d-%02d" % (current_time_minus_1.year, current_time_minus_1.month,current_time_minus_1.day)

job_name2 = 'Cleaning up Partition for S3'
job_description2 = 'Cleaning up Partition for S3'
job_path2 = '/opt/kettle9/transformation/DLY/DropPartition/dropPartitionMainV1.ktr'
job_source2 = 'S3 Bucket ozdbrp00001'
job_destination2 = 'S3 Bucket ozdbrp00001'
job_schedule2 = 'Daily'
job_cmd2 = f'sh /opt/kettle9.4/data-integration/pan.sh -file={job_path2}'
job_runner.kettle_run(job_name2,job_description2,job_path2,job_source2,job_destination2,job_schedule2,job_cmd2)
