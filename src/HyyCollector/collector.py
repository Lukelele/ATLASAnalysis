import pika
import os
import numpy as np
from io import StringIO
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator,AutoMinorLocator
from lmfit.models import PolynomialModel, GaussianModel


def init_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='collector_queue', durable=True)
    return connection, channel




combined_df = pd.DataFrame()

def collect_data(ch, method, properties, body):
    global combined_df
    df = pd.read_json(StringIO(body.decode()))
    combined_df = pd.concat([combined_df, df], ignore_index=True)
    
    os.makedirs('/app/data', exist_ok=True)
    
    file_exists = os.path.isfile("/app/data/output.csv")
    
    # Write DataFrame to CSV
    df.to_csv("/app/data/output.csv", mode='a', index=False, header=not file_exists)
    
    ch.basic_ack(delivery_tag=method.delivery_tag)


connection, channel = init_connection()
channel.basic_consume(queue='collector_queue', on_message_callback=collect_data)
channel.start_consuming()
