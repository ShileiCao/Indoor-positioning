import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset
from sklearn.neighbors import KDTree
from tqdm import tqdm
import pandas as pd
class Model(nn.Module): #RNN
    def __init__(self,
                 wifi_nums,
                 mag_nums,
                 clasi_nums,
                 gru_layers,
                 gru_dims,
                 input_dropout=0.2,
                 dropout=0.2,
                 ):
        super(Model,self).__init__()
        self.wifi_nums=wifi_nums
        self.mag_nums=mag_nums
        self.clasi_nums=clasi_nums
        self.gru_layers=gru_layers
        self.gru_dims=gru_dims
        self.input_dropout=input_dropout
        self.dropout=dropout
        
        self.WIFIdropout=nn.Dropout(self.input_dropout)
        self.gru=nn.GRU(input_size=self.wifi_nums+self.mag_nums,
                        hidden_size=self.gru_dims,
                        num_layers=self.gru_layers,
                        batch_first=True,
                        dropout=self.dropout,
                        bidirectional=False)
        self.classifier=nn.Linear(self.gru_dims,self.clasi_nums)
        self.softmax=nn.Softmax(dim=2)
        
    def forward(self,x):
        # x: (batch_size,seq_len,mag_nums+wifi_nums)
        mag=x[:,:,:self.mag_nums]
        wifi=x[:,:,self.mag_nums:]
        wifi=self.WIFIdropout(wifi)
        x=torch.cat([mag,wifi],dim=2)
        x=self.gru(x)[0]
        return self.softmax(self.classifier(x))
    
class Model2(nn.Module): #RNN
    def __init__(self,
                 wifi_nums,
                 mag_nums,
                 gru_layers,
                 gru_dims,
                 input_dropout=0.2,
                 dropout=0.2,
                 ):
        super(Model2,self).__init__()
        self.wifi_nums=wifi_nums
        self.mag_nums=mag_nums
        self.gru_layers=gru_layers
        self.gru_dims=gru_dims
        self.input_dropout=input_dropout
        self.dropout=dropout
        
        self.WIFIdropout=nn.Dropout(self.input_dropout)
        self.gru=nn.GRU(input_size=self.wifi_nums+self.mag_nums,
                        hidden_size=self.gru_dims,
                        num_layers=self.gru_layers,
                        batch_first=True,
                        dropout=self.dropout,
                        bidirectional=False)
        self.regressor=nn.Linear(self.gru_dims,2)
        
    def forward(self,x):
        # x: (batch_size,seq_len,mag_nums+wifi_nums)
        mag=x[:,:,:self.mag_nums]
        wifi=x[:,:,self.mag_nums:]
        wifi=self.WIFIdropout(wifi)
        x=torch.cat([mag,wifi],dim=2)
        x=self.gru(x)[0]
        return self.regressor(x)
class ModelRNN(nn.Module): #RNN
    def __init__(self,
                 wifi_nums,
                 mag_nums,
                 rnn_layers,
                 rnn_dims,
                 input_dropout=0.2,
                 dropout=0.2,
                 ):
        super(ModelRNN,self).__init__()
        self.wifi_nums=wifi_nums
        self.mag_nums=mag_nums
        self.rnn_layers=rnn_layers
        self.rnn_dims=rnn_dims
        self.input_dropout=input_dropout
        self.dropout=dropout
        
        self.WIFIdropout=nn.Dropout(self.input_dropout)
        self.rnn=nn.RNN(input_size=self.wifi_nums+self.mag_nums,
                        hidden_size=self.rnn_dims,
                        num_layers=self.rnn_layers,
                        batch_first=True,
                        dropout=self.dropout,
                        bidirectional=False)
        self.regressor=nn.Linear(self.rnn_dims,2)
        self.regressor=nn.Linear(self.rnn_dims,2)
        
    def forward(self,x):
        # x: (batch_size,seq_len,mag_nums+wifi_nums)
        mag=x[:,:,:self.mag_nums]
        wifi=x[:,:,self.mag_nums:]
        wifi=self.WIFIdropout(wifi)
        x=torch.cat([mag,wifi],dim=2)
        x=self.rnn(x)[0]
        return self.regressor(x)


class Dset(Dataset):
    def __init__(self, data, tlength, all_xy):
        posis=data[:,:2]
        self.tlength=tlength

        mags=data[:,4:7]
        wifis=data[:,7:]
        wifis=torch.from_numpy(wifis).float()
        mags=torch.from_numpy(mags).float()
        
        posis=torch.from_numpy(posis).float()
        wifis=torch.where(wifis < -100, torch.zeros_like(wifis), wifis)
        wifis=torch.where(wifis == 0, torch.ones_like(wifis)*(-100), wifis)
        wifis=(wifis+100)/100
        wifis=wifis.detach()
        
        self.x=torch.cat([mags,wifis],dim=1)
        self.x=self.x.view(-1,self.tlength,self.x.shape[1])
        
        self.all_xy=all_xy
        self.KDtree=KDTree(self.all_xy)
        
        self.length=self.x.shape[0]
        self.y=self.query_index(posis)
        
        self.y=self.y.view(-1,self.tlength)
        
    def query_index(self,posis):
        ans=[]
        if posis.dim()==1:
            posis=posis.unsqueeze(0)
        for i in tqdm(range(posis.shape[0]),desc='initing'):
            temp=self.KDtree.query([posis[i].numpy()],k=1)[1][0][0]
            ans.append(temp)
        return torch.tensor(ans)
    
    def __len__(self):
        return self.length
    def __getitem__(self, index):
        return self.x[index],F.one_hot(self.y[index],num_classes=len(self.all_xy)).float()
    
class Dset2(Dataset):
    def __init__(self, data, tlength, zooming=0.0001):
        posis=data[:,:2]
        self.tlength=tlength        
        
        self.zooming=zooming
        mags=data[:,4:7]
        wifis=data[:,7:]
        wifis=torch.from_numpy(wifis).float()
        mags=torch.from_numpy(mags).float()
        posis=torch.from_numpy(posis).float()
        wifis=torch.where(wifis < -100, torch.zeros_like(wifis), wifis)
        wifis=torch.where(wifis == 0, torch.ones_like(wifis)*(-100), wifis)
        wifis=(wifis+100)/100
        wifis=wifis.detach()
        mags=torch.sqrt(torch.sum(mags**2,dim=1)).view(-1,1)
        self.x=torch.cat([mags,wifis],dim=1)
        self.x=self.x.view(-1,self.tlength,self.x.shape[1])
        self.y=posis*zooming
        self.y=self.y.view(-1,self.tlength,2)
        self.length=self.x.shape[0]
    
    
    def __len__(self):
        return self.length
    def __getitem__(self, index):
        return self.x[index],self.y[index]

class DsetStreaming(Dataset):
    def __init__(self, data, zooming=0.0001):
        if data is pd.DataFrame:
            data=data.values
        posis=data[:,:2]      
        
        self.zooming=zooming
        mags=data[:,4:7]
        wifis=data[:,7:]
        wifis=torch.from_numpy(wifis).float()
        mags=torch.from_numpy(mags).float()
        posis=torch.from_numpy(posis).float()
        wifis=torch.where(wifis < -100, torch.zeros_like(wifis), wifis)
        wifis=torch.where(wifis == 0, torch.ones_like(wifis)*(-100), wifis)
        wifis=(wifis+100)/100
        wifis=wifis.detach()
        
        self.x=torch.cat([mags,wifis],dim=1)
        # self.x=self.x.view(-1,self.tlength,self.x.shape[1])
        self.y=posis*zooming
        # self.y=self.y.view(-1,self.tlength,2)
        self.length=self.x.shape[0]
    
    
    def __len__(self):
        return self.length
    def __getitem__(self, index):
        return self.x[index],self.y[index]