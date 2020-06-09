import boto3
import pandas as pd
import numpy as np
def lambda_handler(event, context):
	rules = {'threeDayLane' : 0.1, 'lenFromCode' : 6, 'etaDtype': 'Integer', 'lenToCode' : 6, 'oneDayLane': 0.1, 'twoDayLane': 0.8}
	client = boto3.client('s3',aws_access_key_id='<Access_Key>',aws_secret_access_key='<Secret_key>') 
	resource = boto3.resource('s3')
	my_bucket1 = 'stagingbkt'
	key=event['Input']['Key']
	obj1 = client.get_object(Bucket=my_bucket1, Key=key)
	df1 = pd.read_csv(obj1['Body'],names=['Business','Shippment Method','From','To','fromCountry','toCountry','ETA'])
	totalLane=len(df1)
	for i in range(totalLane):
		if len(str(df1.loc[i,'From']))!=rules['lenFromCode'] or len(str(df1.loc[i,'To']))!=rules['lenToCode'] or not isinstance(df1.loc[i,'ETA'], np.int64):
			return "Terminate Flow"
	oneDayLane=(df1['ETA']==1).sum()/totalLane
	twoDayLane=(df1['ETA']==2).sum()/totalLane
	threeDayLane=(df1['ETA']==3).sum()/totalLane
	#print(oneDayLane, twoDayLane, threeDayLane)

	if oneDayLane!= rules['oneDayLane'] or twoDayLane!=rules['twoDayLane'] or threeDayLane!= rules['threeDayLane']:
		return "Approval Flow"
	return "Merge Flow"
