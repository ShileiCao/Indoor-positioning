from model import Model2
import torch
import numpy as np
import json
from scipy.interpolate import splprep, splev
from flask import Flask, request, jsonify
app = Flask(__name__)

position = json.dumps({'0':{'x':str(0),'y':str(0)}})
# init class infer with infer=Infer()
# call infer(json) to get series of points [(x,y)]
# 详细来说，每一次调用call将会返回过去20个调用的平滑路径（共计1000个采样），当过去调用次数不足三次时，会返回None
def init_model():
    Regressor=Model2(
        wifi_nums=383,
        mag_nums=1,
        gru_layers=2,
        gru_dims=128
    )

    Regressor.load_state_dict(torch.load('Regressor99.pth',map_location='cpu'))
    return Regressor

def Mac2Num(mac):
    mac=mac.replace(':','')
    return int(mac,16)

def mac2idx(mac,dic): #mac:string :'00:00:00:00:00:00' -> int: idx in vector
    
    #hex to dec
    mac=Mac2Num(mac)    
    #get idx
    try:
        idx=dic[str(mac)]
    except:
        idx=-1
    return idx

def RSSIPreprocess(wifis):
    wifis=torch.where(wifis < -100, torch.zeros_like(wifis), wifis)
    wifis=torch.where(wifis == 0, torch.ones_like(wifis)*(-100), wifis)
    wifis=(wifis+100)/100
    wifis=wifis.detach()
    return wifis

def macjson2vector(macjson):
    vec=torch.zeros(383)
    wifidic=macjson['WiFi']
    file=open('Mac2Num.json','r')
    dic=json.load(file)
    for wifi in wifidic:
        mac=wifi['BSSID']
        idx=mac2idx(mac,dic)
        if idx==-1:
            continue
        vec[idx]=wifi['SignalStrength']
    vec=RSSIPreprocess(vec)
    return vec

def magjson2vector(magjson):
    magjson=magjson['mag']
    vector=np.array([magjson['x'],magjson['y'],magjson['z']])
    vector=np.linalg.norm(vector)
    vector=torch.tensor([vector]).float()
    return vector

def json2vector(jsonf):
    wifis=jsonf
    mags=jsonf
    wifis=macjson2vector(wifis)
    mags=magjson2vector(mags)
    vector=torch.cat([mags,wifis])
    return vector

class infer():
    def __init__(self,past=[],past_points=[],len_=20):
        self.past=past
        self.past_points=past_points
        self.len=len_
        self.Regressor=init_model()
        
    def _smooth(self):
        points=self.past_points
        points=np.array(points)
        init_x=points[:,0]
        init_y=points[:,1]
        tck, u = splprep([init_x, init_y], s=1,k=3,)
        u_new = np.linspace(u.min(), u.max(), 1000)
        x_new, y_new = splev(u_new, tck, der=0)
        return x_new,y_new
    
    @torch.no_grad()
    def __call__(self,jsonf):
        vector=json2vector(jsonf)
        self.past.append(vector)
        if len(self.past)>self.len:
            self.past.pop(0)
        inpu=torch.stack(self.past,dim=0).float().unsqueeze(0)
        output=self.Regressor(inpu)[0][-1].cpu().numpy()
        self.past_points.append(output)
        if len(self.past_points)>self.len:
            self.past_points.pop(0)
        path_=output*10000
        dic={'0':{'x':str(path_[0]),'y':str(path_[1])}}
        dic=json.dumps(dic)
        return dic
    
@app.route('/receive', methods=['POST'])
def handle_request():
    global position
    data = request.json  # 获取前端发送的JSON数据
    # 处理数据和业务逻辑
    print(data)
    ans=infer(data)
    position = ans
    response_data = {'message': 'Success'}
    return jsonify(response_data)

@app.route('/send', methods=['get'])
def handle_request2():
    print(position)
    return position
    

if __name__ == '__main__':
    #example
    infer=infer()
    app.run(host='0.0.0.0', port=5000)
    
    
    
    
    
        
    