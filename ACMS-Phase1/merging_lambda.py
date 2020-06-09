import boto3
import pandas as pd
from io import StringIO

def lambda_handler(event, context):
    # TODO implement
    client = boto3.client('s3',aws_access_key_id='<Acces_key>',aws_secret_access_key='<Secret_key>') 
    resource = boto3.resource('s3') 
    my_bucket1 = 'stagingbkt'
    key1=event['Input']['Key']    
    obj1 = client.get_object(Bucket=my_bucket1, Key=key1)
    df1 = pd.read_csv(obj1['Body'],names=['Business','Shippment Method','From','To','fromCountry','toCountry','ETA'])
    df1['From-To']=df1['From'].astype(str)+" "+df1['To'].astype(str)
    df1=pd.DataFrame(df1, columns=['From-To','ETA'])
    df1.sort_values("From-To", axis = 0, ascending = True,inplace = True)
    totalLane = len(df1)
    oneDayLane=(df1['ETA']==1).sum()/totalLane
    twoDayLane=(df1['ETA']==2).sum()/totalLane
    threeDayLane=(df1['ETA']==3).sum()/totalLane
    print(oneDayLane, twoDayLane, threeDayLane)
    tagList=client.get_object_tagging( Bucket=my_bucket1, Key=key1)['TagSet']
    for tag in tagList:
        if tag['Key']=="Expiry Date":
                expdt=tag['Value']
                break
    print(expdt)
    totalLane = len(df1)
    oneDayLane=(df1['ETA']==1).sum()/totalLane
    twoDayLane=(df1['ETA']==2).sum()/totalLane
    threeDayLane=(df1['ETA']==3).sum()/totalLane
    print(oneDayLane, twoDayLane, threeDayLane)
    #print(df1)
    my_bucket2 ='datasourcebkt'
    l=key1.split("/")
    print(l)
    dynamokey=""
    for i in range(4):
    	dynamokey+=l[i]+"/"
    dynamokey=dynamokey[:len(dynamokey)-1]
    print(dynamokey)
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    tableVC = dynamodb.Table('VersionControl')
    tableDB = dynamodb.Table('dynamo234')
    try:
        responseVC = tableVC.get_item(
            Key={
                'transport type': dynamokey
            }
        )
    except boto3.dynamodb.exceptions.DynamoDBKeyNotFoundError:
    	responseVC = None 
#     responseVC = tableVC.get_item(
#             Key={
#                 'transport type': dynamokey
#             }
#         )

    if 'Item' not in responseVC.keys():
        print("NO record")
        oneDayAggregate=oneDayLane
        twoDayAggregate=twoDayLane
        threeDayAggregate=threeDayLane
        oneDayMain=twoDayMain=threeDayMain=0
        df1[['From','To']] = df1['From-To'].str.split(expand=True)
        #df1.drop(['From-To'], axis=1, inplace=True)
        res_df=df1[['From', 'To', 'ETA']]
        res_df.sort_values("From", axis = 0, ascending = True,inplace = True)
        
    else:
        itemVC = responseVC['Item']
        print(itemVC)
        responseDB=tableDB.get_item(
                Key={
                    'transport type': dynamokey,
                    'version': "v_"+ str(itemVC['version'])
                }
        )
        itemDB= responseDB['Item']
        print(itemDB)
        csv_name=itemDB["csv file"]
        print(csv_name)
        key2=dynamokey+'/'+csv_name
        print(key2)
        # my_bucket2 ='datasourcebkt'
        #key2 = 's3/US/UPS/UPS_GND/US_US/19_05_2020_23_10.csv'
        obj = client.get_object(Bucket=my_bucket2, Key=key2)    
        df2 = pd.read_csv(obj['Body'],names=['From','To','ETA'])
            #df2=pd.DataFrame(f2List,columns=['From','To','ETA'])
        df2['From-To']=df2['From'].astype(str)+" "+df2['To'].astype(str)
        df2=pd.DataFrame(df2, columns=['From-To','ETA'])
        totalMain=len(df2)
        oneDayMain=(df2['ETA']==1).sum()/totalMain
        twoDayMain=(df2['ETA']==2).sum()/totalMain
        threeDayMain=(df2['ETA']==3).sum()/totalMain
        print(oneDayMain, twoDayMain, threeDayMain)
        M1_M2_M3 = str(oneDayMain)+""+str(twoDayMain)+""+str(threeDayMain)
        #print(df2)   
            
        res_df = pd.merge(df1, df2, how = 'outer', on= 'From-To', suffixes= ('_m', '_n'))
        res_df['ETA'] = res_df['ETA_m'].where(res_df['ETA_n'].isnull(), res_df['ETA_n'])
        res_df.drop(['ETA_m', 'ETA_n',], axis= 1, inplace= True)
        res_df['ETA']=res_df['ETA'].astype(int)
        res_df[['From','To']] = res_df['From-To'].str.split(expand=True)
        res_df.drop(['From-To'], axis=1, inplace=True)
        res_df=res_df[['From','To','ETA']]
        #print(res_df)
        res_df.sort_values("From", axis = 0, ascending = True,inplace = True)
        totalAgg = len(res_df)
        oneDayAggregate=(res_df['ETA']==1).sum()/totalAgg
        twoDayAggregate=(res_df['ETA']==2).sum()/totalAgg
        threeDayAggregate=(res_df['ETA']==3).sum()/totalAgg
        print(oneDayAggregate, twoDayAggregate, threeDayLane)


    oneDayDiff=abs(oneDayAggregate-oneDayMain)
    twoDayDiff=abs(twoDayAggregate-twoDayMain)
    threeDayDiff=abs(threeDayAggregate-threeDayMain)
    print(oneDayDiff, twoDayDiff, threeDayDiff)

    L1_L2_L3 = str(oneDayLane)+"_"+str(twoDayLane)+"_"+str(threeDayLane)
    A1_A2_A3 = str(oneDayAggregate)+"_"+str(twoDayAggregate)+"_"+str(threeDayAggregate)
    D1_D2_D3 = str(oneDayDiff)+"_"+str(twoDayDiff)+"_"+str(threeDayDiff)


    csv_buffer = StringIO()
    res_df.to_csv(csv_buffer, header=False,index=False)

    client.put_object(Body=csv_buffer.getvalue(),ContentType='text/csv',Bucket=my_bucket2,Key=key1)
    client.put_object_tagging( Bucket=my_bucket2,
                                            Key=key1,
                                            Tagging={
                                                    'TagSet': [
                                                            {
                                                                    'Key': 'L1_L2_L3',
                                                                    'Value': L1_L2_L3
                                                            },
                                                                    {
                                                                    'Key': 'A1_A2_A3',
                                                                    'Value': A1_A2_A3
                                                            },
                                                                            {
                                                                    'Key': 'D1_D2_D3',
                                                                    'Value': D1_D2_D3
                                                            },
                                                                            {
                                                                    'Key': 'ExpiryDate',
                                                                    'Value': expdt
                                                            }
                                                            ]
                                                    }
                                            )