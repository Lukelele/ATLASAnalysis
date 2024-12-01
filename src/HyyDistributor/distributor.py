import pika
import uproot
import pandas as pd
import numpy as np
import json


def init_connection():
    # establish connection to the rabbitmq server
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    return connection, channel


def send_task(channel, data):
    # send the data to the worker
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=data,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        )
    )
    
    
# read the data from the root file and send it to the worker
def prep_task(channel, tuple_path, samples_list, fraction=0.8):
    for val in samples_list:
        fileString = tuple_path+val+".GamGam.root"
        print("Processing: "+val)
        tree = uproot.open(fileString + ":mini")
        numevents = tree.num_entries
        for data in tree.iterate(["photon_pt","photon_eta","photon_phi","photon_E","photon_isTightID","photon_etcone20"], library="pd", entry_stop=numevents*fraction, step_size=10000):
            # convert numpy arrays to lists
            for col in ["photon_pt","photon_eta","photon_phi","photon_E","photon_isTightID","photon_etcone20"]:
                data[col] = data[col].apply(lambda x:x.tolist() if isinstance(x, np.ndarray) else x)
            # send the data in json format
            send_task(channel, data.to_json())

    


fraction = 0.8

tuple_path = "https://atlas-opendata.web.cern.ch/atlas-opendata/samples/2020/GamGam/Data/" # web address
samples_list = ['data_A','data_B','data_C','data_D']
# samples_list = ['data_A']
    
    
connection, channel = init_connection()
prep_task(channel, tuple_path, samples_list, fraction)

