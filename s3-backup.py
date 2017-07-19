#!/usr/bin/python3
import datetime
import subprocess
import os
import shutil
import sys
import boto3
import logging
client = boto3.client('s3')
s3 = boto3.resource('s3')

##$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$### CONFIGURATION PART BY USER ###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#----------------------------------------------------------------------------------------------------------------------------------------------
#Daily Backup Configuration.(Specify 1 to turn on and 0 to turn off daily)
Daily = {'Sun':1,'Mon':0,'Tue':1,'Wed':1,'Thu':0,'Fri':1,'Sat':1}
#                                                                         
############## Weekly Backup Configuration.###################################
Weekly = {'Sun':1,'Mon':1,'Tue':1,'Wed':1,'Thu':1,'Fri':0,'Sat':0}
#                                                                         
############## Monthly Backup Configuration.##################################
#Take montly backup on the first and/or fifteenth day of a month. (Specify 1 to turn on and 0 to turn off Monthly backup)
Monthly_1 = 1
Monthly_15 = 1
############## MYSQL##############################################                                                                        
#Mysql database backup (Specify database names in single quotes 
#sepereated by commas)
Take_whole_DB_backup = 0  # Value '1' will take whole mysql DB backups on the server
# and the following variable 'mysql_DBS' can be left as it is.
#If Take_whole_DB_backup is enabled and if you want to omit some DBs like default DBs, include those DBs in list 'DB_Exception' below.
DB_Exception = ['information_schema','performance_schema','mysql']
mysql_DBS = ['suitecrm_dev','rentboun_db']
DB_user = 'root'
DB_password = 'ideamine'

################# FILE BACKUP #######################################
#Directories to be backed up.(Specify folder paths in single quotes 
#sepereated by commas)
Doc_Roots = ['/root/AWS-AMI-new','/root/AWS-AMI']  
                                                                   
################ Specify a Local server Directoy ####################
Local_Backup_Dir = '/backup' 

################ S3 Bucket Configuration #############################
S3_Bucket = 'toji-backup'
################ Enable/Disable Local Backup #########################
Lockal_Backup = 1 #value '1' will store backups locally.

################ Enable/Disable Backup retention and specify Retention period##
#
# Set '0' to enable unlimited backup retntion. Other digits are considered as Retention period.
#
Daily_Retention = 1    	# No. of Daily backups
Weekly_Retention = 1	# No. of Weekly Backups
Monthly_Retention = 1	# No. of Monthly backups

############# Retention Calculation ######################
Weekly_Retention = Weekly_Retention*7
Monthly_Retention = Monthly_Retention*30    

########################## Log File #######################
LOG_FILE = '/var/log/s3-backup.log'
#----------------------------------------------------------------------------------------------------------------------------------------------
##$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


#Declare log file configuration
logging.basicConfig(filename=LOG_FILE,level=logging.INFO,format="%(asctime)s:%(levelname)s:%(message)s")
logging.info(' ')
logging.info('BACKUP STARTS FOR THE DAY')
logging.info(' ')

####Remove Temporary backup files###################
def Remove_Temp_Files():
  print('Removing temporary files.')
  os.chdir(Local_Backup_Dir)			
  BACKUPS = ['File-Backup','DB-Backup']
  for FilesDBs in BACKUPS:
    subprocess.Popen('rm -rf '+FilesDBs, shell=True)
    logging.info('Removing temporary backup file, '+FilesDBs)
		

#####   MYSQL PART   ####
#Mysql Backup 
def mysql_Backup(DB_name):
  try:
    time_now =  datetime.datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    d=subprocess.Popen("mysqldump "+" -u"+DB_user+" -p"+DB_password+" --force --opt "+ DB_name+" > "+ Local_Backup_Dir +'/DB-Backup/'+DB_name+"-"+time_now+".sql", shell=True)
    d.wait()
    d.communicate()
    if(d.returncode != 0):
    	raise
    print("Database Backup Success for DB:",DB_name)
    logging.info('Creating mysql backup for '+DB_name+' : Success')
			
  except:
    print("Database Backup failed for DB:",DB_name)
    logging.error('Creating mysql backup for '+DB_name+' : Failed')

#Executon
def BACKUP_DB():
  os.chdir(Local_Backup_Dir)
  if not os.path.exists('DB-Backup'):
    os.makedirs('DB-Backup')
  print('')
  print('Taking Database backups')
  logging.info('Starting MySql backup')
  for DB in mysql_DBS:
    mysql_Backup(DB)
  print('MySql backup complete..')
  logging.info('MySql backup comple')
  print('')


######   WEB ROOT PART   ########


def BACKUP_DIR():
  #try:
	#  os.makedirs(Local_Backup_Dir+'/'+'File-Backup')
  #except:
  #  print('File-Backup Folder exists')
  for Dir in Doc_Roots:
    Time_now =  datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    Folder_Name = Dir.rstrip('/').split('/')[-1]
    Folder_Path = os.path.split(Dir.rstrip('/'))[-2]
    shutil.make_archive(Local_Backup_Dir+'/File-Backup/'+Folder_Name+'-'+Time_now,'zip',Folder_Path,Folder_Name)
    print('Archive created for the directory ''"',Dir,'"')
    logging.info('Archive created for the directory : '+Dir)

########Check S3 Connection ###################
#------------------------------------------------------
Remove_Temp_Files()

try:
  print("Checking S3 Bucket connection..")
  Connect_s3 = client.list_buckets()
  S3_BKTS = str([ i['Name'] for i in Connect_s3['Buckets'] ])
  print("Available S3 Buckets are", S3_BKTS)
  logging.info('S3 Bucket successfully connected. Available Buckets :'+S3_BKTS)
  print('')
except:
  print("Failed S3 login, Check AWS-CLI configuration")
  logging.info('Failed S3 login, Check AWS-CLI configuration')
  print('')
  sys.exit()

#--------------------------------
#Create Local backup directories.
#--------------------------------
Backup_Folders = ['Daily','Weekly','Monthly']
if Lockal_Backup:
	os.chdir(Local_Backup_Dir)
	for Local_Folder in Backup_Folders:
        	if os.path.exists(Local_Folder):
                	print ('Local backup directory ',Local_Folder,' Exists!')
                	logging.info('Local backup directory '+Local_Folder+' Exists!')
        	else:
                	os.makedirs(Local_Folder)
                	print ('Local backup directory ',Local_Folder,' Created')
                	logging.info('Local backup directory '+Local_Folder+' Created')

#--------------------------------
#Check whether whole Mysql DB backup is enabled or not.
#--------------------------------
if Take_whole_DB_backup == 1:
	print('Script is configured to take Entire DB backup on the server')
	d = subprocess.Popen("mysql -e 'SHOW DATABASES;' | tr -d '|' | grep -v Database", shell = True,stdout=subprocess.PIPE)
	result = d.communicate()[0]
	result = str(result)
	result = result.rstrip("\\n'")
	result = result.lstrip("b'")
	mysql_DBS = result.split('\\n')
	mysql_DBS = list(filter(lambda x: x not in DB_Exception ,mysql_DBS))
	logging.info('Script is configured to take Entire DB backup on the server. DBs are '+str(mysql_DBS))
else:
	print('Script is configured to take only spcified DB backup on the server')
	logging.info('Script is configured to take only spcified DB backup on the server. DBs are '+str(mysql_DBS))

#############################################       
#Copy Backups to Local and S3 Directories.
#############################################
def COPY_BACKUPS(Folder,Retention):
  Time_now =  datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
  bucket = s3.Bucket(S3_Bucket)
  BACKUPS = ['File-Backup','DB-Backup']
  for FilesDBs in BACKUPS:
    os.chdir(Local_Backup_Dir)
    print('Copying backup files to S3 Bucket:',S3_Bucket)
    logging.info('Copying backup files to S3 Bucket:'+S3_Bucket)
    for root, dirs, files in os.walk(FilesDBs):
      for File in files:
        print('Uploading', root+'/'+File)
        logging.info('Uploading file '+root+'/'+File)
        client.upload_file(root+'/'+File,S3_Bucket, Folder+'/'+Time_now+'/'+root+'/'+File)
    print(' ')
    if Retention:
      print('Checking S3 Backup Retention')
      logging.info('Retention enabled. Checking S3 Backup Retention period')
      e= client.list_objects(Bucket=S3_Bucket,Prefix=Folder)
      for i in e['Contents']:
	      Folder_time = str(i['LastModified']).split(' ')[0]
	      Folder_time = datetime.datetime.strptime(Folder_time, "%Y-%m-%d")
	      TIME_NOW = datetime.datetime.now()
	      D = TIME_NOW - Folder_time
	      Days=int(D.days)
	      if Days > Retention:
		      print('Removing old file in S3',i['Key'],'as per Retention period',Retention,'Days')
		      logging.info('Removing old file in S3 '+i['Key']+' as per Retention period '+str(Retention)+' Days')
		      response = bucket.delete_objects(Delete={'Objects': [{'Key': i['Key']}]})
	      else:
		      logging.info('Not removing '+i['Key']+' as it comes under retention period')
    else:
      print('Backup Retention is not enabled. No old backups shall be removed from S3 Bucket')
      logging.info('Backup Retention is not enabled. No old backups shall be removed from S3 Bucket')
    print(' ')	
    if Lockal_Backup:
      print('Lockal backup is enabled in the server')
      logging.info('Lockal backup is enabled in the server')
      shutil.copytree(FilesDBs,Local_Backup_Dir+'/'+Folder+'/'+Time_now+'/'+FilesDBs)
      print('Copying backup files to Local Backup Directory...')
      logging.info('Copying backup files to Local Backup Directory')
      if Retention:
        print('Removing backups older than',Retention,'days from local server')
        logging.info('Removing backups older than '+str(Retention)+' days from local server')
        wait = subprocess.Popen('find '+Local_Backup_Dir+'/'+Folder+'/* -mtime +'+str(Retention),shell=True)
        wait.wait()
        wait.communicate()
        subprocess.Popen('find '+Local_Backup_Dir+'/'+Folder+'/* -mtime +'+str(Retention)+' -exec rm -rf {} \; > /dev/null 2>&1', shell=True)
        print(' ')
				
      else:
      	print('Backup Retention is not enabled. No old backups shall be removed from local server')
      	logging.info('Backup Retention is not enabled. No old backups shall be removed from local server')
				
    else:
      print('Lockal backup is not enabled in the server')
      logging.info('Lockal backup is not enabled for the server')
      subprocess.Popen('rm -rf '+FilesDBs, shell=True)	


######################################
#Checking Daily backup configuration.#
######################################
print('')
print('#'*35)
print('Checking Daily backup configuration')
logging.info('Checking Daily backup configuration')
print('#'*35)
print('')
Temp_Same_Day = 0
Temp_Same_Month_1 = 0
Temp_Same_Month_15= 0

for Day in Daily:
	if Daily.get(Day) == 1 and Day == datetime.date.today().strftime("%a"):
		print('Dalily Bacup Configured for '+Day+' and its about to start')
		logging.info('Dalily Bacup Configured for '+Day+'. Starting Daily backup')
		BACKUP_DIR()
		BACKUP_DB()
		COPY_BACKUPS('Daily',Daily_Retention)
#Check if weekly backup is configured for the same day.

		if Weekly.get(Day) == 1:
			Temp_Same_Day = 1
			print('')
			print('Copying Daily backup to weekly as backups are configured for same day')
			logging.info('Copying Daily backup to weekly as backups are configured for same day')
			print('-'*69)
			COPY_BACKUPS('Weekly',Weekly_Retention)
		else:
			Temp_Same_Day = 0

#Check if monthly backup is configured for the same day.

		if Monthly_1 == 1 and datetime.date.today().strftime("%d") == '13':
			print('Monthly backup for the first day is configured. Starting Monthly backup')
			logging.info('Monthly backup for the first day is configured. Starting Monthly Backup')
			Temp_Same_Month_1 = 1
			print('')
			print('Copying Daily backup to Monthly as backups are configured for same day')
			print('-'*70)
			logging.info('Copying Daily backup to Monthly as backups are configured for same day')
			COPY_BACKUPS('Monthly',Monthly_Retention)
		else:
			Temp_Same_Month_1 = 0


		if Monthly_15 == 1 and datetime.date.today().strftime("%d") == '15':
			print('Monthly backup for the fifteenth day is configured. Starting monthly backup')
			print('')
			logging.info('Monthly backup for the fifteenth day is configured. Starting monthly backup')
			Temp_Same_Month_15= 1
			print('Copying Daily backup to Montly as backups are configured for same day')
			print('-'*70)
			logging.info('Copying Daily backup to Montly as backups are configured for same day')
			COPY_BACKUPS('Monthly',Monthly_Retention)
		else:
			Temp_Same_Month_15= 0
			
		Remove_Temp_Files()
	else:
		print('No Daily backup configured for '+Day)
		logging.info('No Daily backup configured for '+Day)
#Remove_Temp_Files()
print(' ')
print('='*50)
print('Normal Weekly and Monthly backup checks start here')
logging.info('Normal Weekly and Monthly backup checks start here')
print('='*50)
#########################################
#Check Weekly backup configuration.######
#########################################
if not Temp_Same_Day:
	print('')
	print('#'*35)
	print('Checking Weekly backup configuration...')
	logging.info('Checking Weekly backup configuration')
	print('#'*35)
	print('')
	for Day in Weekly:
		if Weekly.get(Day) == 1 and Day == datetime.date.today().strftime("%a"):
			print('Weekly Bacup Configured for '+Day+' and its about to start')
			logging.info('Weekly Bacup Configured for '+Day+'. Starting weekly backup')
			BACKUP_DIR()
			BACKUP_DB()
			COPY_BACKUPS('Weekly',Weekly_Retention)
		else:
			print('No Weekly backup configured for '+Day)
			logging.info('No Weekly backup configured for '+Day)
else:
  print('Weekly backup already complete as daily and weekly backups are configured for the same day')
  logging.info('Weekly backup already complete as daily and weekly backups are configured for the same day')
#Remove_Temp_Files()
#####################################
#Check Monthly backup configuration.#
#####################################

os.chdir(Local_Backup_Dir)			
subprocess.Popen('rm -rf DB-Backup/*', shell=True)
logging.info('Removing temporary DB backups')

if not Temp_Same_Month_1:
  print(' ')
  print('#'*46)
  print('Checking Monthly(1st day) backup configuration')
  logging.info('Checking Monthly(1st day) backup configuration')
  print('#'*46)
  print('')
  if Monthly_1 == 1 and datetime.date.today().strftime("%d") == '11':
  	print('Monthly backup for the first day is configured. Starting monthly backup')
  	print('-'*71)
  	logging.info('Monthly backup for the first day is configured. Starting monthly backup')
  	BACKUP_DIR()
  	BACKUP_DB()
  	COPY_BACKUPS('Monthly',Monthly_Retention)
  else:
  	print('No Monthly backup for the first day is configured')
  	logging.info('No Monthly backup for the first day is configured')


if not Temp_Same_Month_15:
  print('')
  print('#'*47)
  print('Checking Monthly(15th day) backup configuration')
  print('#'*47)
  logging.info('Checking Monthly(15th day) backup configuration')
  if Monthly_15 == 1 and datetime.date.today().strftime("%d") == '15':
    print('')
    print('Monthly backup for the fifteenth day is configured. Starting backup')
    print('-'*75)
    logging.info('Monthly backup for the fifteenth day is configured. Starting backup')
    BACKUP_DIR()
    BACKUP_DB()
    COPY_BACKUPS('Monthly',Monthly_Retention)

  else:
    print('')
    print('No Monthly backup configured for the fifteenth day.')
    logging.info('No Monthly backup configured for the fifteenth day.')
    
Remove_Temp_Files()
print(' ')

