# Python script to take DB and file backups to AWS S3 bucket

This script takes directory and database backup of Linux server especially for bare metal server and it can be stored either locally or Amazon S3 Bucket. The main features of this script are.

1. Mysql databases to be backed up can be specified in script. If you want to take the backups of each and every DB backups, thats also possible. DB exceptions can also be specified.

2.User can Ebable or Disable local server backup.

3.Backup retention can be specified for Daily,Weekly and Monthly backups seperately. Retention is common for both local and S3 bucket.
  
  
Server Requirements     
===================     
1. pip3  #[ apt-get install python3-pip ]
2. Boto3 #[ pip3 install boto3 ]
3. AWS CLI #[ pip install awscli ; aws configure ]
3. Python3              
5. Need to create and specify Local backup directory.
6. Need to create and specify S3 bucket.
