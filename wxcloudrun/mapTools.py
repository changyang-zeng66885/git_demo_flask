from geopy.distance import geodesic
import requests
import config
import json
from wxcloudrun import db
from wxcloudrun.kmeans import KMeans



# 获取两点之间的直线距离
def getLineDistance(c1,c2):
    #c1 = "121.455718,31.249574"
    #c2 = "121.475507,31.228228"
    try:
        latlng1 = tuple(map(float, c1.split(',')))
        latlng2 = tuple(map(float, c2.split(',')))

        lat, lng = latlng1[0], latlng1[1]
        latlng1 = (lng, lat)
        lat, lng = latlng2[0], latlng2[1]
        latlng2 = (lng, lat)
        distance = geodesic(latlng1, latlng2).kilometers
        return distance      
    except:
        print(f"Intputs '{c1}'or'{c2}' not legal")
        return -1

# 获取两点间的步行通勤时间
def getWalkPath(startC,endC):
    url = "https://restapi.amap.com/v3/direction/walking"
    params = {
        "origin": startC,
        "destination": endC,
        "key": config.amap_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            time = data['route']['paths'][0]['duration']
            path = data['route']['paths'][0]['steps']
            time = float(time)/3600
            #print('Time:',data['route']['paths'][0]['duration'])
            #print('route:',data['route']['paths'][0]['steps'])
            return time,path
        else:
            print("无可行道路")
            return -1,{}
    else:
        print("请求失败，状态码:", data['status']) 
    time = 999999
    path = []
    data = {}
    return time,data['status']

# 公交规划
def getPublicTransitPath(startC,endC):
    url = "https://restapi.amap.com/v3/direction/transit/integrated"
    params = {
        "origin": startC,
        "destination": endC,
        "key": config.amap_key,
        "city":"021"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        #print(data)
        if data['status'] == '1':
            time = data['route']['transits'][0]['duration']
            path = data['route']['transits'][0]['segments'][0]
            time = float(time)/3600 # 将时间秒转化为小时
            return time,path
        else:
            print("无可行道路")
            return -1,[]
    else:
        print("请求失败，状态码:", data['status']) 
    time = 999999
    path = []
    return time,data['status']


# 获取最优通勤方式（步行/公交）
# 给的两点经纬度startC/endC,最大步行距离MAX_WALK_DISTANCE,获取两点间的通勤时间(小时)，以及最优路线
def getCommutePath(startC,endC,MAX_WALK_DISTANCE=1.2):
    lineDistance = getLineDistance(startC,endC)
    if lineDistance <= MAX_WALK_DISTANCE:
        time,path = getWalkPath(startC,endC)
        return time,path,"walk"
    else:
        time,path = getPublicTransitPath(startC,endC)
        return time,path,"publicTransit"
    
# 使用贪心算法获得一天之内景点的路径
def getPathNN(spot_list,startC,endC,MAX_TIME=12,MAX_WALK_DISTANCE=1.1):
    # 获取景点信息（`spot_id`, `spot_name`, `tour_time`, `pos`，perf）
    spot_dict_perf = {spot["spot_id"]: spot["pref"] for spot in spot_list} 
    spot_id_list = [spot["spot_id"] for spot in spot_list]
    spot_id_str = ", ".join(str(spot_id) for spot_id in spot_id_list)
    sql_query = "SELECT `spot_id`, `spot_name`, `tour_time`, `pos` FROM `flask_demo`.`Spot` WHERE spot_id IN ("+spot_id_str+");"
    res = db.engine.execute(sql_query)
    rows = res.fetchall()
    spot_c_dict = {}
    for row in rows:
        spot_id = row['spot_id']
        spot_c_dict[spot_id] = {
            'spot_name': row['spot_name'],
            'tour_time': row['tour_time'],
            'pos': row['pos'],
            'pref':spot_dict_perf[spot_id]
        }
    # print('spot_c_dict',spot_c_dict)
    # print(spot_c_dict[3]['pos'])
        
    num_spots = len(spot_id_list)    
    visited_spots = set()
    total_time = 0
    total_preference = 0
    max_preference = -1
    current_spot = -1

    # 寻找一个喜爱程度最大的可行点
    for spot in spot_id_list:
        preference = spot_c_dict[spot]['pref']
        start_spotC = spot_c_dict[spot]['pos']

        if preference > max_preference:
            time1,path_1,method_1 = getCommutePath(startC,start_spotC,MAX_WALK_DISTANCE)            
            tour_time = spot_c_dict[spot]['tour_time']
            time2,_,_ = getCommutePath(start_spotC,endC,MAX_WALK_DISTANCE)
            tour_time = float(tour_time)
            if time1 + tour_time + time2 <= MAX_TIME:
                max_preference = preference
                current_spot = spot
                total_time = time1 + tour_time

    if current_spot == -1 :
        print("No valid path")
        return []
        
    visited_spots.add(current_spot)
    route = [current_spot]
    route_detail = [{"Step":f"Start point ->({current_spot}){spot_c_dict[current_spot]['spot_name'] }",
                    "Time": time1,"Method":method_1,"Path":path_1},
                {"Step":f"In {spot_c_dict[spot]['spot_name']}",
                "Time":tour_time,"Method":"-"}]
        
    while len(visited_spots) < num_spots:
        #print(f"Current route:{route}")
        max_preference = -1
        nearest_spot = None
        currentC = spot_c_dict[current_spot]['pos']
        for next_spot in spot_id_list:
            if next_spot not in visited_spots:
                preference = spot_c_dict[next_spot]['pref']                
                if preference > max_preference:
                    #print(f"Try {next_spot}")
                    nextC = spot_c_dict[next_spot]['pos']                    
                    t_cn,_,_ = getCommutePath(currentC,nextC,MAX_WALK_DISTANCE)   # 获取current_spot->next_spot 的时间 t_cn                         
                    t_n = spot_c_dict[next_spot]['tour_time']                 # 获取在next_spot 游玩的时间 t_n            
                    t_ne,_,_ = getCommutePath(nextC,endC,MAX_WALK_DISTANCE)   # 获取next_spot-> end_spot 的时间 t_ne
                    t_n = float(t_n)
                    if total_time + t_cn+ t_n + t_ne <= MAX_TIME:
                        max_preference = preference
                        nearest_spot = next_spot
            
        if nearest_spot != None:                        
            total_preference += max_preference
            nearstC = spot_c_dict[nearest_spot]['pos']
            t_cn,path_cn,method_cn = getCommutePath(startC,nearstC,MAX_WALK_DISTANCE)        
            t_n = spot_c_dict[nearest_spot]['tour_time'] 
            t_n = float(t_n)
            route_detail.append({"Step":f"({current_spot}){spot_c_dict[current_spot]['spot_name'] }->({nearest_spot}){spot_c_dict[nearest_spot]['spot_name'] }",
                                "Time": t_cn,"Method":method_cn,"Path":path_cn})
            
            route_detail.append({"Step":f"In ({nearest_spot}){spot_c_dict[nearest_spot]['spot_name'] }",
                                "Time":t_n,"Method":"-"})           
            total_time = total_time + t_cn+ t_n                       
            current_spot = nearest_spot
            visited_spots.add(current_spot)
            route.append(current_spot)
            
        else:
            break
        
    currentC = spot_c_dict[current_spot]['pos']
    t_ne,path_ne,method_ne = getCommutePath(currentC,endC,MAX_WALK_DISTANCE)
    route_detail.append({"Step":f"({current_spot}){spot_c_dict[current_spot]['spot_name'] }-> end point",
                        "Time": t_ne,"Method":method_ne,"Path":path_ne})
    total_time = total_time + t_ne
    route_short = ['Startpoint']+[spot_c_dict[spot]['spot_name'] for spot in route]+['endPoint']
    return total_preference, route,route_short,route_detail,total_time

# k-means聚类函数
def kmeans_spots(spot_list,k):

    # 获取景点信息（`spot_id`, `spot_name`, `tour_time`, `pos`，perf）
    spot_dict_perf = {spot["spot_id"]: spot["pref"] for spot in spot_list} 
    spot_id_list = [spot["spot_id"] for spot in spot_list]
    spot_id_list_sorted = sorted(spot_id_list)
    spot_id_str = ", ".join(str(spot_id) for spot_id in spot_id_list)
    sql_query = "SELECT `spot_id`, `spot_name`, `tour_time`, `pos` FROM `flask_demo`.`Spot` WHERE spot_id IN ("+spot_id_str+");"
    res = db.engine.execute(sql_query)
    rows = res.fetchall()
    spot_c_dict = {}
    for row in rows:
        spot_id = row['spot_id']
        spot_c_dict[spot_id] = {
            'spot_name': row['spot_name'],
            'tour_time': row['tour_time'],
            'pos': row['pos'],
            'pref':spot_dict_perf[spot_id]
        }
    coordinates = [v["pos"] for k, v in spot_c_dict.items()]      
    lats = [float(coord.split(',')[1].strip()) for coord in coordinates]
    lngs = [float(coord.split(',')[0].strip()) for coord in coordinates]   
    data = list(zip(lats, lngs))
    
    # 使用KMeans进行聚类
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(data)
    labels = kmeans.predict(data)
    
    daily_plan_dict = {}
    # labels:[1 1 1 2 0 0 1 1 1 1 0 2]
    for i in range(len(labels)):
        if labels[i] not in daily_plan_dict:
            daily_plan_dict[labels[i]] = set()
        daily_plan_dict[labels[i]].add(spot_id_list_sorted[i])
    return daily_plan_dict 
    # daily_plan_dict = {1: {0, 3, 20, 54}, 0: {25, 2, 23, 7}, 2: {9, 77}}

# 工具函数，get_mulitDays_route()函数需要用到
def extract_values(route_dict):
    result_set = set()  # 创建一个空集合
    [result_set.update(value) for value in route_dict.values()]  # 使用列表推导式和update()方法提取所有值
    return result_set

# 获取多天的路径
def get_mulitDays_route(spot_list,D,startC,endC,MAX_TIME = 12, MAX_WALK_DISTANCE = 2):

    # 获取景点信息（`spot_id`, `spot_name`, `tour_time`, `pos`，perf）
    spot_dict_perf = {spot["spot_id"]: spot["pref"] for spot in spot_list} 
    spot_id_list = [spot["spot_id"] for spot in spot_list]
    spot_id_str = ", ".join(str(spot_id) for spot_id in spot_id_list)
    sql_query = "SELECT `spot_id`, `spot_name`, `tour_time`, `pos` FROM `flask_demo`.`Spot` WHERE spot_id IN ("+spot_id_str+");"
    res = db.engine.execute(sql_query)
    rows = res.fetchall()
    spot_c_dict = {}
    for row in rows:
        spot_id = row['spot_id']
        spot_c_dict[spot_id] = {
            'spot_name': row['spot_name'],
            'tour_time': row['tour_time'],
            'pos': row['pos'],
            'pref':spot_dict_perf[spot_id]
        }
    
    planning = []
    count = 0
    pref_high = set([k for k, v in spot_c_dict.items() if v["pref"] >= 0.8]) # 获取喜爱程度>0.8的景点列表
    total_spots = spot_id_list

    planning_short = []

    while not D-count == 0: 
        daily_plan_dict = kmeans_spots([spot for spot in spot_list if spot["spot_id"] in total_spots],
                                       k = D-count)    
        c1 = daily_plan_dict[0]
        total_preference, route,route_short,route_detail,total_time = getPathNN([spot for spot in spot_list if spot["spot_id"] in list(c1)],
                                                                     startC,endC, MAX_TIME,MAX_WALK_DISTANCE)        
        c1_star = set(route)    
        #print("Best route:",c1_star)
        c1_h = c1.intersection(pref_high)
        set1 = c1_h.difference(c1_star)
        set2 = extract_values(daily_plan_dict).difference(c1)
        total_spots = set2.union(set1)    
        planning.append({"Day":count+1,"route":route,"route_short":route_short,"route_detail":route_detail,"Total_time":total_time})
        planning_short.append({"Day":count+1,"route_short":route_short,"Total_time":total_time,'total_preference':total_preference})
        count += 1
        print(f"Planning for day {count} /{D} is Done")

    #return {'spot_c_dict':spot_c_dict,'pref_high':str(pref_high),'total_spots':total_spots}
    return planning,planning_short


    





    
    
