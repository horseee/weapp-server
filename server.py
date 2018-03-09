# encoding=utf8
from flask import Response
from flask import Flask, jsonify
from flask import abort
from flask import request, make_response
from flask import url_for, render_template
from werkzeug.utils import secure_filename
import pymysql
import requests
import os

app = Flask(__name__)
db= pymysql.connect(host="localhost",user="root", password="maxinyin",db="loreal",port=3306,charset='utf8')
cur = db.cursor()


@app.route("/mp3/<name>")
def streamwav(name):
    def generate():
        fwav = open(name, "rb")
        data = fwav.read(1024)
        while data:
            yield data
            data = fwav.read(1024)
    return Response(generate(), mimetype="audio/mpeg")

@app.route("/search", methods = ['GET'])
def get_search_result():
    searchword = request.args.get('keyword')
    search_sql = "select * from User where Name like '%" + searchword + "%'"
    result_rows = cur.execute(search_sql)
    searchusers = []
    for i in range(result_rows):
        row = cur.fetchone()
        [name, avatar, user_id, score, province, city] = [row[1], row[3], row[0], row[7],row[8], row[9]]
        user = {
            'id': user_id,
            'name' : name,
            'avatar' :  avatar,
            'like' : 0,
            'post' : 0,
            'score': score,
            'province':province,
            'city':city
        }
        searchusers.append(user)
    
    for i in range(result_rows):
        user_id = searchusers[i]['id']
        user_like_total = "select * from Post_Like where post_user_id = " + str(user_id)
        like_number = cur.execute(user_like_total)
    
        user_post = "select * from Post where UserID = " + str(user_id)
        post_number = cur.execute(user_post)
        
        searchusers[i]['like'] = like_number
        searchusers[i]['post'] = post_number        

    return jsonify({'User': searchusers}), 201

@app.route("/update-score", methods = ['POST'])
def update_score():
    score_update = "update User set Score = Score + " + str(request.json['score']) + " where ID = " + str(request.json['id'])
    print(score_update)
    cur.execute(score_update)
    return 'update success', 201

@app.route("/detail")
def get_post_detail():
    user_id = request.args.get('userid')
    post_id = request.args.get('postid')
    post_select_sql = "select * from Post where PostID = " + str(post_id)
    cur.execute(post_select_sql)
    res = cur.fetchone()
    [title, detail, likenumber] = [res[1], res[2], res[7]]
    image_list = []
    if res[3] != '':
        url_res = res[3].split('/root/loreal-server/')
        image_list.append("https://www.horseee.top/image/" + url_res[1])
    if res[4] != '':
        url_res = res[4].split('/root/loreal-server/')
        image_list.append("https://www.horseee.top/image/" + url_res[1])
    if res[5] != '':
        url_res = res[5].split('/root/loreal-server/')
        image_list.append("https://www.horseee.top/image/" + url_res[1])
    t = res[8]
    post_time = t.strftime("%m-%d %H:%M")

    user_select = "select * from User where ID = " + str(res[6])
    cur.execute(user_select)
    user_res = cur.fetchone()
    [origin_user_id, nickname, avatar] = [user_res[0],user_res[1], user_res[3]]
    
    like_select = "select * from Post_Like where postid = " + str(post_id) + " and userid = " + str(user_id) 
    like_bo = cur.execute(like_select)
    if like_bo > 0:
        upstatus = 1
    else:
        upstatus = 0
    
    post_detail = {
        'title': title,
        'detail': detail,
        'like': likenumber,
        'image':image_list,
        'time':post_time,
        'name':nickname,
        'avatar': avatar,
        'originid': origin_user_id,
        'upstatus': upstatus
    }

    return jsonify({'detail': post_detail}), 201

@app.route("/contest_number_<question_id>", methods=['GET'])
def get_contest_number(question_id):
    sql_count_contest = "select * from Contest_1 where top_question = "+ str(question_id)
    contest_num = cur.execute(sql_count_contest)
    return str(contest_num), 201

@app.route("/user_info")
def get_user_like():
    user_inf = []
    user_id = request.args.get('userid')
    user_like_total = "select * from Post_Like where post_user_id = " + str(user_id)
    like_number = cur.execute(user_like_total)
    
    user_post = "select * from Post where UserID = " + str(user_id)
    post_number = cur.execute(user_post)

    user_score = "select * from User where ID = "+ str(user_id)
    cur.execute(user_score)
    info = cur.fetchone()

    now_user = {
        'like': like_number,
        'saying': post_number,
        'score': info[7]
    }

    user_inf.append(now_user)
    return jsonify({'info': user_inf}), 201

@app.route("/like-change", methods = ['POST'])
def changeLike():
    print(request.json)
    if request.json['status'] == 0:
        like_delete = "delete from Post_Like where userid = " + str(request.json['userid']) + " and postid = " + str(request.json['postid'])
        cur.execute(like_delete)
        like_delete_in_Post = "update Post set LikeCount = LikeCount - 1 where PostID = " + str(request.json['postid'])
        cur.execute(like_delete_in_Post) 
    else: 
        like_insert ="insert into Post_Like(userid, postid, post_user_id) values ('" + str(request.json['userid']) + "','" + str(request.json['postid']) + "','" + str(request.json['postuserid']) + "');"
        cur.execute(like_insert)
        like_insert_in_Post = "update Post set LikeCount = LikeCount + 1 where PostID = " + str(request.json['postid'])
        cur.execute(like_insert_in_Post)
    db.commit()
    return "success", 201

@app.route("/contest/login_<id>", methods = ['POST'])
def Add_contest_user(id):
    print(request.json)
    sql_count = "select * from Contest_" + str(id) + ";"
    num = cur.execute(sql_count)
    if num >= 30:
        return 'full', 201
    try:
        sql_insert = "insert into Contest_" + id + "(UserID, AvatarUrl,top_question) values ('" + str(request.json['userid']) + "','" + request.json['avatarurl']  + "','0');"
        cur.execute(sql_insert)
        db.commit()
    except: 
        return 'fail', 201
    return 'success', 201

@app.route("/contest_correct", methods=['POST'])
def get_correct_contest():
    print(request.json)
    sql_update_contest_user = "update Contest_1 set top_question = " + str(request.json['question_id']) +" where UserID = " + str(request.json['userID'])
    cur.execute(sql_update_contest_user)
    db.commit()
    return "success", 201

@app.route("/contest/exit_<id>", methods = ['POST'])
def Delete_contest_user(id):
    try:
        sql_delete = "delete from Contest_" + id + " where UserID = " + str(request.json['userid'])
        cur.execute(sql_delete)
        db.commit()
    except:
        return 'fail', 201
    return 'success', 201

@app.route("/new-post", methods = ['Post'])
def create_Post():
    sql_count = "select * from PostCount"
    cur.execute(sql_count)  
    Next_ID = (cur.fetchone())[0]+1
    print("NextPostID: "+ str(Next_ID))

    url_list = request.json['image']
    if len(url_list) < 3:
        for i in range(3 - len(url_list)):
            url_list.append('')
    print(url_list)

    sql_insert = "insert into Post(PostID, Title, Detail, ImageUrl_0, ImageUrl_1,ImageUrl_2, UserID, LikeCount, PostTime) values ('" + str(Next_ID) + "','" + request.json['title'] + "','" + request.json['detail'] + "','" + url_list[0] + "','" + url_list[1] + "','" + url_list[2] + "','" + str(request.json['id']) + "','0','" + request.json['posttime'] + "')"
    status = cur.execute(sql_insert)
    if status == 1:
        sql_update = "update PostCount set num = '"+ str(Next_ID) +"'"
        cur.execute(sql_update)  
        db.commit()
        return str(Next_ID), 201
    else: 
        return 'sql insert fail', 201

@app.route("/login", methods = ['POST'])
def create_User():
    print(request.json)
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
    
    judge_if_exist = "select * from User where OpenID = '" + openid + "'"
    user_num = cur.execute(judge_if_exist)
    if user_num > 0:
        return str(cur.fetchone()[0]), 201
    
    sql_insert ="insert into User(ID, Name, OpenID, AvatarUrl, StuID, Level, LikeCount, Score, province, city) values('" + str(Next_ID) + "','" + request.json['UserName'] + "','"+ openid + "','"+ request.json['UserUrl'] +"','" + request.json['StudentID']+"','1','0','0','" +request.json['province']+"','" + request.json['city'] + "')"
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
   
@app.route("/image/<path_image>")
def get_image(path_image):
    image = open("{}".format(path_image), "rb")
    resp = Response(image, mimetype="image/jpeg")
    return resp

@app.route("/image/uploads/<path_image>")
def get_upload_image(path_image):
    image = open("uploads/{}".format(path_image), "rb")
    resp = Response(image, mimetype="image/jpeg")
    return resp

@app.route("/hot/<int:hotpage>")
def get_Hot(hotpage):
    request_user_id = request.args.get('userid')
    Posts = []
    sql_select_hot = "(select * from (select * from Post order by LikeCount desc limit " + str(hotpage * 10) + "," + str((hotpage+1) * 10)+ ") p left join User u on p.UserID = u.ID) order by p.LikeCount desc;"
    num = cur.execute(sql_select_hot)

    for i in range(num):
        temp_row = cur.fetchone()
        post_id = temp_row[0]
        title = temp_row[1]
        detail = temp_row[2]
        url = []
        for j in range(3):
            url_whole = temp_row[3 + j]
            if (url_whole == ''):
                url.append('')
            else:
                url_res = url_whole.split('/root/loreal-server/')
                url.append("https://www.horseee.top/image/" + url_res[1])
        userID = temp_row[6]
        LikeCount = temp_row[7]

        posttime = temp_row[8]
        t = str(posttime.hour) + ":" + str(posttime.minute)


        month = ['Jan', 'Feb', 'Mar', 'April', 'May', 'June', 'July', 'Aug','Sept','Oct','Nov', 'Dec'] 
        m = month[posttime.month-1]

        [nickname, avatar] = [temp_row[10], temp_row[12]]
        
        now_post = {
            'postid' : post_id,
            'title': title,
            'detail' : detail,
            'url_1' : url[0],
            'url_2' : url[1],
            'url_3' : url[2],
            'postuserid' : userID,
            'name' : nickname,
            'avatarUrl' : avatar,
            'LikeCount' : LikeCount,
            'month': m,
            'day': posttime.day,
            'daytime': posttime.strftime("%H:%M"),
            'upstatus': 0
        }        

        Posts.append(now_post)

    for i in range(len(Posts)):
        like_count = "select * from Post_Like where postid = " + str(Posts[i]['postid']) + " and userid = " + str(request_user_id)
        num = cur.execute(like_count)
        if num > 0:
            Posts[i]['upstatus'] = 1

    return jsonify({'posts': Posts}), 201


@app.route("/new/<int:newpage>")
def get_New(newpage):
    News = []
    request_user = request.args.get('userid')
    sql_select_new = "(select * from (select * from Post order by PostTime desc limit " + str(newpage * 10) + "," + str((newpage+1) * 10)+ ") p left join User u on p.UserID = u.ID) order by PostTime desc;"
    num = cur.execute(sql_select_new)

    for i in range(num):
        new_row = cur.fetchone()
        post_id = new_row[0]
        title = new_row[1]
        detail = new_row[2]
        url = []
        for j in range(3):
            url_whole = new_row[3 + j]
            if (url_whole == ''):
                url.append('')
            else:
                url_res = url_whole.split('/root/loreal-server/')
                url.append("https://www.horseee.top/image/" + url_res[1])
        userID = new_row[6]
        LikeCount = new_row[7]

        newtime = new_row[8]
        t = str(newtime.hour) + ":" + str(newtime.minute)

        month = ['Jan', 'Feb', 'Mar', 'April', 'May', 'June', 'July', 'Aug','Sept','Oct','Nov', 'Dec']
        m = month[newtime.month-1]

        [nickname, avatar] = [new_row[10], new_row[12]]
        
        new_post = {
            'postid' : post_id,
            'title': title,
            'detail' : detail,
            'url_1' : url[0],
            'url_2' : url[1],
            'url_3' : url[2],
            'postuserid' : userID,
            'name' : nickname,
            'avatarUrl' : avatar,
            'LikeCount' : LikeCount,
            'month': m,
            'day': newtime.day,
            'daytime': newtime.strftime("%H:%M"),
            'upstatus': 0
        }        
        News.append(new_post)

    for i in range(len(News)):
        like_count = "select * from Post_Like where postid = " + str(News[i]['postid']) + " and userid = " + str(request_user)
        num = cur.execute(like_count)
        if num > 0:
            News[i]['upstatus'] = 1
    return jsonify({'news': News}), 201

@app.route("/userpost")
def get_User_post():
    UserPosts = []
    request_user = request.args.get('userid')
    seleced_user = request.args.get('selectid')
    user_info_select = "select * from User where ID = " + str(seleced_user)
    cur.execute(user_info_select)
    userinfo = cur.fetchone()
    [name, avatar] = [userinfo[1], userinfo[3]]
    
    sql_select_user = "select * from Post where UserID = " + str(seleced_user) + " order by PostTime desc;"
    num = cur.execute(sql_select_user)

    for i in range(num):
        new_row = cur.fetchone()
        post_id = new_row[0]
        title = new_row[1]
        detail = new_row[2]
        url = []
        for j in range(3):
            url_whole = new_row[3 + j]
            if (url_whole == ''):
                url.append('')
            else:
                url_res = url_whole.split('/root/loreal-server/')
                url.append("https://www.horseee.top/image/" + url_res[1])
        userID = new_row[6]
        LikeCount = new_row[7]

        newtime = new_row[8]
        t = str(newtime.hour) + ":" + str(newtime.minute)

        month = ['Jan', 'Feb', 'Mar', 'April', 'May', 'June', 'July', 'Aug','Sept','Oct','Nov', 'Dec']
        m = month[newtime.month-1]
        
        user_post = {
            'postid' : post_id,
            'title': title,
            'detail' : detail,
            'url_1' : url[0],
            'url_2' : url[1],
            'url_3' : url[2],
            'postuserid' : userID,
            'name' : name,
            'avatarUrl' : avatar,
            'LikeCount' : LikeCount,
            'month': m,
            'day': newtime.day,
            'daytime': newtime.strftime("%H:%M"),
            'upstatus': 0
        }        
        UserPosts.append(user_post)

    for i in range(len(UserPosts)):
        like_count = "select * from Post_Like where postid = " + str(UserPosts[i]['postid']) + " and userid = " + str(request_user)
        num = cur.execute(like_count)
        if num > 0:
            UserPosts[i]['upstatus'] = 1
    return jsonify({'news': UserPosts}), 201

@app.route("/question/<time>")
def get_Question(time):
    questions = []

    sql_count = "select * from QuestionList where useDate = '" + time +"'"
    question_num = cur.execute(sql_count) 

    for i in range(question_num): 
        QueInf = cur.fetchone()
        question = {
            'question_id':QueInf[5],
            'detail': QueInf[0],
            'A': QueInf[1],
            'B': QueInf[2],
            'C': QueInf[3],
            'answer': QueInf[7],
            'time': QueInf[4],
            'id': QueInf[8]
        }
        questions.append(question)
    #print(questions)
    return jsonify({'questions': questions}), 201

@app.route('/upload', methods=['POST'])
def upload():
    print(request)
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        upload_path = os.path.join(basepath,r'uploads',secure_filename(f.filename))
        f.save(upload_path)
        print(upload_path)
        return upload_path ,200
    return 'fail', 404

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000, debug=True)
