from geopy.distance import geodesic
import requests
import config

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

# 获取两点间的通勤时间
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
            return time,path,data
        else:
            print("无可行道路")
    else:
        print("请求失败，状态码:", data['status']) 
    time = 999999
    path = []
    return time,path,data




