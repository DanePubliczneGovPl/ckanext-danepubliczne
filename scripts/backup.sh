db=ckan
remote_user=USER_ON_BACKUP_SERVER
backup_server=BACKUP_SERVER_HOST

timestamp=`date +%Y%m%dT%H%M%S`
logfile=/var/log/ckan/backup.log
base_dir=/home/ckan/backup/

echo "Backing up 'ckan' database to $remote_user@$backup_server:/home/$remote_user/data/$timestamp-$db.pgdump" >> $logfile

sudo -u postgres pg_dump --format=custom $db | sudo -u ckan ssh $remote_user@$backup_server -C "cat > /home/$remote_user/data/$timestamp-$db.pgdump"


# echo "Backing up resources to       $remote_user@$backup_server:/home/$remote_user/data/$timestamp-fs.tar.gz" >> $logfile

# One day incremental backup will be needed probably: http://www.gnu.org/software/tar/manual/html_node/Incremental-Dumps.html
# tar -cz -C /home/ckan/data datapusher.db resources storage | sudo -u ckan ssh $remote_user@$backup_server -C "cat > /home/$remote_user/data/$timestamp-fs.tar.gz"

echo "-- Finished backup started at $timestamp" >> $logfile
