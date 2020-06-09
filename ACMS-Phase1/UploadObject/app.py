from flask import Flask, render_template, request
import boto3
from datetime import datetime
#from werkzeug import secure_filename
app = Flask(__name__)

@app.route('/')
def upload_file():
   return render_template('upload.html')
	
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file2():
   if request.method == 'POST':
      f = request.files['file']
      expdt=request.form['ExpiryDate']
      dt = datetime.strptime(expdt, '%Y-%m-%d')
      print(expdt)
      name=f.filename
      fname=name.split('-')
      my_bucket1 = 'stagingbkt'
      cname=fname[0]
      bname=fname[1]
      smeth=fname[2]
      fromTo=fname[3]
      key=cname+"/"+bname+"/"+smeth+"/"+fromTo+"/"+fname[4]

      #s3 = boto3.resource('s3') 
      s3=boto3.client('s3')
      s3.upload_fileobj(f, my_bucket1, key, ExtraArgs={'ContentType':'text/csv' })
      s3.put_object_tagging( Bucket=my_bucket1,Key=key,Tagging={'TagSet': [{'Key': 'Country Name','Value': cname},{'Key': 'Business Name','Value': bname},{'Key': 'Shipment Method','Value': smeth},{'Key': 'From-To','Value': fromTo},{'Key':'Expiry Date','Value':expdt}]})
      client = boto3.client('stepfunctions',region_name='us-east-2') #low-level functional API
      client.start_execution(stateMachineArn='<StateMachine_arn>',input='{"Key":"'+key+'"}')
      return 'file uploaded successfully'
		
if __name__ == '__main__':
   app.run(debug = True)