db=piwik
remote_user=USER_ON_BACKUP_SERVER
backup_server=BACKUP_SERVER_HOST

timestamp=`date +%Y%m%dT%H%M%S`
logfile=/var/log/ckan/backup.log
base_dir=/home/ckan/backup/

echo "Backing up '$db' database to $remote_user@$backup_server:/home/$remote_user/data/$timestamp-$db.sql.gz" >> $logfile

mysqldump $db | gzip -8 | sudo -u ckan ssh $remote_user@$backup_server -C "cat > /home/$remote_user/data/$timestamp-$db.sql.gz"

echo "-- Finished backup started at $timestamp" >> $logfile
