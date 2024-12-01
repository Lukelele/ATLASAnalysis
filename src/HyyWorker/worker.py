import pika
import time
import math
import numpy as np
import pandas as pd
import json
import uproot



def calc_myy(photon_pt,photon_eta,photon_phi,photon_E):
    # first photon is [0], 2nd photon is [1] etc
    px_0 = photon_pt[0]*math.cos(photon_phi[0]) # x-component of photon[0] momentum
    py_0 = photon_pt[0]*math.sin(photon_phi[0]) # y-component of photon[0] momentum
    pz_0 = photon_pt[0]*math.sinh(photon_eta[0]) # z-component of photon[0] momentum
    px_1 = photon_pt[1]*math.cos(photon_phi[1]) # x-component of photon[1] momentum
    py_1 = photon_pt[1]*math.sin(photon_phi[1]) # y-component of photon[1] momentum
    pz_1 = photon_pt[1]*math.sinh(photon_eta[1]) # z-component of photon[1] momentum
    sumpx = px_0 + px_1 # x-component of diphoton momentum
    sumpy = py_0 + py_1 # y-component of diphoton momentum
    sumpz = pz_0 + pz_1 # z-component of diphoton momentum 
    sump = math.sqrt(sumpx**2 + sumpy**2 + sumpz**2) # magnitude of diphoton momentum 
    sumE = photon_E[0] + photon_E[1] # energy of diphoton system
    return math.sqrt(sumE**2 - sump**2)/1000 #/1000 to go from MeV to GeV


def cut_photon_reconstruction(photon_isTightID):
    return photon_isTightID[0]==True and photon_isTightID[1]==True
    
def cut_photon_pt(photon_pt):
    return photon_pt[0]>40000 and photon_pt[1]>30000

def cut_isolation_et(photon_etcone20):
    return photon_etcone20[0]<4000 and photon_etcone20[1]<4000

def cut_photon_eta_transition(photon_eta):
    return (abs(photon_eta[0])>1.52 or abs(photon_eta[0])<1.37) and (abs(photon_eta[1])>1.52 or abs(photon_eta[1])<1.37)


def apply_cut(data):
    nIn = len(data.index)
        
    # Cut on photon reconstruction quality using the function cut_photon_reconstruction defined above
    data = data[np.vectorize(cut_photon_reconstruction)(data.photon_isTightID)]
    
    # Cut on transverse momentum of the photons using the function cut_photon_pt defined above
    data = data[np.vectorize(cut_photon_pt)(data.photon_pt)]
    
    # Cut on energy isolation using the function cut_isolation_et defined above
    data = data[np.vectorize(cut_isolation_et)(data.photon_etcone20)]
    
    # Cut on pseudorapidity inside barrel/end-cap transition region using the function cut_photon_eta_transition
    data = data[np.vectorize(cut_photon_eta_transition)(data.photon_eta)]
    
    # Calculate reconstructed diphoton invariant mass using the function calc_myy defined above
    data['myy'] = np.vectorize(calc_myy)(data.photon_pt,data.photon_eta,data.photon_phi,data.photon_E)
    
    nOut = len(data.index)
    
    return data



def process_data(ch, method, properties, body):
    process_dict = json.loads(body.decode())
    global tree_dict
    tree = tree_dict[process_dict["file"]]
    
    data_all = pd.DataFrame()
    for data in tree.iterate(["photon_pt","photon_eta","photon_phi","photon_E",
                            "photon_isTightID","photon_etcone20"], # add more variables here if you want to use them
                           library="pd", # choose output type as pandas DataFrame
                           entry_start=process_dict["start"], # start at this event
                           entry_stop=process_dict["end"]):
        for col in ["photon_pt","photon_eta","photon_phi","photon_E","photon_isTightID","photon_etcone20"]:
                data[col] = data[col].apply(lambda x:x.tolist() if isinstance(x, np.ndarray) else x)

        nIn = len(data.index) # number of events in this batch
        
        # Cut on photon reconstruction quality using the function cut_photon_reconstruction defined above
        data = data[ np.vectorize(cut_photon_reconstruction)(data.photon_isTightID)]
        
        # Cut on transverse momentum of the photons using the function cut_photon_pt defined above
        data = data[ np.vectorize(cut_photon_pt)(data.photon_pt)]
        
        # Cut on energy isolation using the function cut_isolation_et defined above
        data = data[ np.vectorize(cut_isolation_et)(data.photon_etcone20)]
        
        # Cut on pseudorapidity inside barrel/end-cap transition region using the function cut_photon_eta_transition
        data = data[ np.vectorize(cut_photon_eta_transition)(data.photon_eta)]
        
        # Calculate reconstructed diphoton invariant mass using the function calc_myy defined above
        data['myy'] = np.vectorize(calc_myy)(data.photon_pt,data.photon_eta,data.photon_phi,data.photon_E)
        
        data_all = pd.concat([data_all, data], ignore_index=True)

        nOut = len(data.index) # number of events passing cuts in this batch

    print(nIn, nOut)
    
    collector_channel = connection.channel()
    collector_channel.queue_declare(queue='collector_queue', durable=True)
    
    collector_channel.basic_publish(
        exchange='',
        routing_key='collector_queue',
        body=data_all.to_json(),
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        )
    )
    
    ch.basic_ack(delivery_tag=method.delivery_tag)
    

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

samples_list = ['data_A','data_B','data_C','data_D']
tree_dict = {}
for i in samples_list:
    tuple_path = "https://atlas-opendata.web.cern.ch/atlas-opendata/samples/2020/GamGam/Data/"
    fileString = tuple_path+i+".GamGam.root"
    tree = uproot.open(fileString + ":mini")
    tree_dict[i] = tree

channel.queue_declare(queue='task_queue', durable=True)
# Ensure fair dispatch
channel.basic_qos(prefetch_count=1)
    
channel.basic_consume(queue='task_queue', on_message_callback=process_data)
channel.start_consuming()

