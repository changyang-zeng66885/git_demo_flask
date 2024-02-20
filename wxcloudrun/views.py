from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters,Spot
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.mapTools import getWalkPath,getPublicTransitPath,getCommutePath,getPathNN,kmeans_spots,get_mulitDays_route
from wxcloudrun.kmeans import KMeans
from sqlalchemy import text
from wxcloudrun import db
import json
import math

################### 单人旅行线路规划 #######################
#根据余弦相似度,获取某人的待选景点pref值

# TypeError: The view function did not return a valid response. 
# The return type must be a string, dict, tuple, Response instance, 
# or WSGI callable, but it was a list.
@app.route('/api/route/get_spot_list_pref',methods = ['POST'])
def get_spot_list_pref():
    data = request.get_json()
    user_id = data.get('user_id')
    try:
        sql_query = text("SELECT u_weiyi,u_lishi,u_ziran,u_yule,u_guanguang FROM `flask_demo`.`User` where user_id = "+user_id+";")
        result = db.engine.execute(sql_query).first()
        result_dict = dict(result)
        user_pref = [result_dict['u_weiyi'],result_dict['u_lishi'],result_dict['u_ziran'],result_dict['u_yule'],result_dict['u_guanguang']]
    except:
        user_pref = [0,0,0,0,0]

    spot_id_list = data.get('spot_id_list')
    spot_id_list = list(spot_id_list)
    spot_list = []
    for spot_id in spot_id_list:
        sql_query = text(f"SELECT s_weiyi,s_lishi,s_ziran,s_yule,s_guanguang FROM `flask_demo`.`Spot` where spot_id = {spot_id};")
        try:
            result = db.engine.execute(sql_query).first()
            result_dict = dict(result)
            spot_pref = [result_dict['s_weiyi'],result_dict['s_lishi'],result_dict['s_ziran'],result_dict['s_yule'],result_dict['s_guanguang']]

            # 计算余弦相似度
            dot_product = sum(a * b for a, b in zip(user_pref, spot_pref))
            norm_user = math.sqrt(sum(a**2 for a in user_pref))
            norm_spot = math.sqrt(sum(b**2 for b in spot_pref))       
            cosine_similarity = dot_product / (norm_user * norm_spot)
        except:
            cosine_similarity = 0
        spot_list.append({"spot_id":spot_id,'pref':cosine_similarity})
    
    return {'spot_list':spot_list}

# 单人单天路径规划
@app.route('/api/route/getRouteForSingleDay',methods=['POST'])
def getSingleDayRoute():
    data = request.get_json()
    startC = data.get('startC')
    endC = data.get('endC')
    spot_list = data.get('spot_list')
    # 获取可选参数，如果没有传入则使用默认值
    MAX_TIME = data.get('MAX_TIME', 12)
    MAX_WALK_DISTANCE = data.get('MAX_WALK_DISTANCE', 1.2)

    # startC = "121.506554,31.249768"
    # endC = "121.496554,31.249768"
    # spot_list=[
    #     {"spot_id": 0 , "pref": 0.99},
    #     {"spot_id": 9, "pref": 0.45},
    #     {"spot_id": 25, "pref": 0.88},
    #     {"spot_id": 2, "pref": 0.45},
    #     {"spot_id": 3, "pref": 0.41},
    #     {"spot_id": 7, "pref": 0.33},
    #     {"spot_id": 20, "pref": 0.4},
    #     {"spot_id": 54, "pref": 0.33},
    #     {"spot_id": 23, "pref": 0.7},
    #     {"spot_id": 77, "pref": 0.82}
    # ]
    # MAX_TIME=12
    # MAX_WALK_DISTANCE=1.1

    total_preference, route,route_short,route_detail,total_time = getPathNN(spot_list,startC,endC,MAX_TIME,MAX_WALK_DISTANCE)
    return {'total_preference':total_preference, 'route':route,'route_short':route_short,'route_detail':route_detail,'total_time':total_time}

@app.route('/api/route/getRouteForMultiDay',methods=['POST'])
def getRouteForMultiDay():
    data = request.get_json()
    startC = data.get('startC')
    endC = data.get('endC')
    spot_list = data.get('spot_list')
    Ndays = data.get('Ndays')
    # 获取可选参数，如果没有传入则使用默认值
    MAX_TIME = data.get('MAX_TIME', 12)
    MAX_WALK_DISTANCE = data.get('MAX_WALK_DISTANCE', 1.2)


    # spot_list=[
    #     {"spot_id": 0, "pref": 0.99},
    #     {"spot_id": 9, "pref": 0.45},
    #     {"spot_id": 25, "pref": 0.88},
    #     {"spot_id": 2, "pref": 0.45},
    #     {"spot_id": 3, "pref": 0.41},
    #     {"spot_id": 7, "pref": 0.33},
    #     {"spot_id": 20, "pref": 0.4},
    #     {"spot_id": 54, "pref": 0.33},
    #     {"spot_id": 23, "pref": 0.7},
    #     {"spot_id": 77, "pref": 0.82}
    # ]
    # startC = "121.506554,31.249768"
    # endC = "121.496554,31.249768"
    # Ndays = 3
    # MAX_TIME = 12
    # MAX_WALK_DISTANCE = 2

    planning,planning_short = get_mulitDays_route(spot_list,Ndays,startC,endC,MAX_TIME = 12, MAX_WALK_DISTANCE = 2)
    return {'Days':Ndays,'planning':planning,'planning_short':planning_short}


################### 用户相关 #######################
#用户登录    OK
@app.route('/api/user/login',methods = ['POST'])
def user_login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    print('user_id: ',user_id)
    sql_query = text("SELECT password FROM `flask_demo`.`User` where user_id = "+user_id+";")

    try:
        result = db.engine.execute(sql_query).first()
        result_dict = dict(result)
        # print(result_dict['password'])
        if str(result_dict['password']) == str(password) :
            return {'status':1,'message':"OK"}
        else:
            return {'status':0,'message':"WRONG PASSWORD!"}
    except:
        return {'status':-1,'message':f"NO SUCH USER '{user_id}'"}

# 用户信息查询OK
@app.route('/api/user/userinfo',methods = ['GET'])
def getUserInfo():
    user_id = int(request.args.get('user_id'))
    sql_query = text(f"SELECT * FROM flask_demo.User where user_id = {user_id};")
    try:
        result = db.engine.execute(sql_query).first()
        result_dict = dict(result)
        result_json = json.dumps(result_dict,ensure_ascii=False)
        return {'status':1,'user_info':result_dict}

    except:
        return {'status':0,'user_info':{}}

################### 景点相关 #######################
# 根据景点spot_id获取景点信息OK
@app.route('/api/spot/getspotById',methods = ['GET'])
def getspotById():
    spot_id = int(request.args.get('spot_id'))
    sql_query = text(f"SELECT * FROM flask_demo.Spot where spot_id = {spot_id};")
    try:
        result = db.engine.execute(sql_query).first()
        result_dict = dict(result)
        result_json = json.dumps(result_dict,ensure_ascii=False)
        return {'status':1,'spot_info':result_dict}
    except:
        return {'status':0,'spot_info':{}}

# 景点的模糊搜索
@app.route('/api/spot/getspotByName', methods=['GET'])
def getspotByByName():
    spot_name = request.args.get('spot_name')
    
    # 更改SQL查询语句实现模糊搜索
    sql_query = text(f"SELECT spot_id,spot_name,hotness FROM flask_demo.Spot WHERE spot_name LIKE '%{spot_name}%';")
    try:
        result = db.engine.execute(sql_query).fetchall()
        
        # 将结果转换为字典列表
        result_list = [dict(row) for row in result]
        result_json = json.dumps(result_list, ensure_ascii=False)
        
        return {'status': 1, 'spot_info': result_list}
    except:
        return {'status': 0, 'spot_info': []}



@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')

@app.route('/api/sayhello',methods = ['GET'])
def sayHello():
    name = str(request.args.get('name'))
    if name:
        return 'Hello ' + name
    else:
        return 'Please provide a name in the query parameter.'





###########################################################################
#####################下面是测试的代码######################################
##########################################################################
@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)
