import MySQLdb
import datetime, time

db = MySQLdb.connect(host="localhost",
                     user="ci",
                     passwd="password",
                     db="pitest_ci")


## Required format
## date, mutations, killed, survived, no coverage, timed out

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

#INSERT INTO pitest_ci.build_result (time, mutations, killed, survived, no_coverage, timed_out, output) VALUES (1,2,3,4,5,6,'This is a test');

# you must create a Cursor object. It will let
#  you execute all the queries you need
cur = db.cursor()

add(1, 2, 3, 4, 5, 6)

# Use all the SQL you like
cur.execute("SELECT * FROM build_result")

# print all the first cell of all the rows
#for row in cur.fetchall():
#    print row[1]

db.close()