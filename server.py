from flask import Response
from flask import Flask, jsonify
from flask import abort
from flask import request, make_response
from flask import url_for
import pymysql
import requests

app = Flask(__name__)
db= pymysql.connect(host="localhost",user="root", password="maxinyin",db="loreal",port=3306,charset='utf8mb4')
cur = db.cursor()


@app.route("/mp3")
def streamwav():
    def generate():
    	id = 1
    	while id < 10:
	    	fwav = open(str(id)+".wav", "rb")
	    	data = fwav.read(1024)
	    	while data:
	    		yield data
	    		data = fwav.read(1024)
	    	id = id + 1
    return Response(generate(), mimetype="audio/x-wav")

@app.route("/login", methods = ['POST'])
def create_User():
	sql_count = "select * from UserCount"
	cur.execute(sql_count)  
	Next_ID = (cur.fetchone())[0]+1
	print("NextID: "+ str(Next_ID))

	url = "https://api.weixin.qq.com/sns/jscode2session?" + "appid=wx4963f019e8e86a05&" + "secret=7474d82965d28cee0e05136c92ea0cb0&" + "grant_type=authorization_code&" + "js_code=" + request.json['LoginCode']
	r = requests.get(url)
	openid_str = r.content.decode()
	start_pos = openid_str.find("openid") + 9
	end_pos = openid_str.find("}")-1
	openid = openid_str[start_pos:end_pos]
	print(openid)

	if openid.find("errmsg") >= 0:
		return '-1', 201

	sql_insert ="insert into User(ID, Name, OpenID, AvatarUrl, StuID) values('" + str(Next_ID) + "','" + request.json['UserName'] + "','"+ openid + "','"+ request.json['UserUrl'] +"','" + request.json['StudentID']+"')"
	status = cur.execute(sql_insert)   
	sql_update = "update UserCount set num = '"+ str(Next_ID) +"'"
	cur.execute(sql_update)  
	db.commit() 

	if status==1:
		return str(Next_ID), 201 
	else:
		return '-1', 201
    # return jsonify({'task': task}), 201
    # 
    # 
@app.route("/image/<int:imageid>.jpg")
def get_image(imageid):
    image = open("image/{}.jpg".format(imageid), "rb")
    resp = Response(image, mimetype="image/jpeg")
    return resp

@app.route("/question/<time>")
def get_Question(time):
	questions = []

	sql_count = "select * from QuestionList where useDate = '" + time +"'"
	cur.execute(sql_count) 

	for i in range(4): 
		QueInf = cur.fetchone()
		question = {
			'id':QueInf[6],
			'detail': QueInf[0],
			'A': QueInf[1],
			'B': QueInf[2],
			'C': QueInf[3],
			'D': QueInf[4],
			'time': QueInf[5],
		}
		questions.append(question)
	print(questions)
	return jsonify({'questions': questions}), 201

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000, debug=True)