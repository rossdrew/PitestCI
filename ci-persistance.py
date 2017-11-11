import MySQLdb
import datetime, time

db = MySQLdb.connect(host="localhost",
                     user="ci",
                     passwd="password",
                     db="pitest_ci")

def create(databaseName):
	try:
		cur.execute("""CREATE TABLE `{}` (
					     `id` int(11) NOT NULL AUTO_INCREMENT,
					     `time` datetime NOT NULL,
					     `mutations` int(11) NOT NULL,
					     `killed` int(11) NOT NULL,
					     `survived` int(11) NOT NULL,
					     `no_coverage` int(11) NOT NULL,
					     `timed_out` int(11) NOT NULL,
					     `output` mediumblob NOT NULL,
					     PRIMARY KEY (`id`)
					   ) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;""".format(databaseName))
		db.commit()
		print("Database '{}' created!".format(databaseName))
	except Exception error:
		print("ERROR: Database '{}' could not be created: {}".format(databaseName, str(error)))
		db.rollback()


def add(mutations, killed, survived, no_coverage, timed_out, xmlBuildOutput):
	try:
		time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		insertCommand = "INSERT INTO `pitest_ci`.`build_result` (time, mutations, killed, survived, no_coverage, timed_out, output) VALUES ('{0}',{1},{2},{3},{4},{5},{6});"
		cur.execute(insertCommand.format(time, mutations, killed, survived, no_coverage, timed_out, xmlBuildOutput))
		db.commit()
		print ("Build information enterred at {}".format(time))
	except Exception as error:
		print ("Build information failed to save: {}".format(str(error)))
		db.rollback() 
	return

# Cursor object to create queries
cur = db.cursor()

add(1, 2, 3, 4, 5, 6)
#cur.execute("SELECT * FROM build_result")

db.close()