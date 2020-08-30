import socket
import os
import struct
import sys
import time
import datetime
import json
import requests
import ast


def main():
    os.environ['REQUESTS_CA_BUNDLE'] = '/run/secrets/kubernetes.io/serviceaccount/service-ca.crt'
    
    with open('/run/secrets/kubernetes.io/serviceaccount/token', 'r') as le_file:
        kubectl_token = le_file.read()
    
    with open('/usr/src/app/reciever-daemonset.yaml', 'r') as le_file2:
        ds_yaml = le_file2.read()
    
    daemonsets_url = "https://kubernetes.default.svc/apis/apps/v1/namespaces/multicast-test/daemonsets"
    verify_kube_ssl = True
    
    kube_request_headers = {
        "Content-Type": "application/yaml",
        "Authorization": f"Bearer {kubectl_token}"
    }
    
    create_ds = requests.request('POST', daemonsets_url, headers=kube_request_headers, data=ds_yaml, verify=verify_kube_ssl)
    
    sys.stdout.write(f'Daemonset creation Status:\n\n{json.loads(create_ds.content)}\n')
    
    # Giving daemonset 180s max to create itself properly
    
    get_ds = requests.request('GET', f'{daemonsets_url}/reciever', headers=kube_request_headers, verify=verify_kube_ssl)
    desiredPodsNumber = json.loads(get_ds.content)["status"]["desiredNumberScheduled"]
    
    while desiredPodsNumber == 0:
        time.sleep(1)
        get_ds = requests.request('GET', f'{daemonsets_url}/reciever', headers=kube_request_headers, verify=verify_kube_ssl)
        desiredPodsNumber = json.loads(get_ds.content)["status"]["desiredNumberScheduled"]
    
    for i in range(0,59):
        numberPodsReady = json.loads(get_ds.content)["status"]["numberReady"]
        sys.stdout.write(f'GET status: Desired: {desiredPodsNumber} ~~~~ Ready: {numberPodsReady}\n')
        if (desiredPodsNumber == numberPodsReady):
            break
        time.sleep(3)
        get_ds = requests.request('GET', f'{daemonsets_url}/reciever', headers=kube_request_headers, verify=verify_kube_ssl)
    
    # Sending multicast message
    message = "Whats up its from the pizza?"
    multicast_group = (os.environ['MULTICAST_GROUP'], int(os.environ['SOCK_PORT']))
    sock_timeout = 3
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(sock_timeout)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    
    messages_recieved = []
    num_of_messages = 0
    kube_cluster_name = os.environ['NODE_NAME'].split('.')[1]
    
    while num_of_messages < 5:
        messages_recieved.append([])
        sys.stdout.write(f'sending message: {message} to multicast group on {datetime.datetime.now().time()} \n')
        sent = sock.sendto(message.encode(), multicast_group)
        sys.stdout.write('waiting to recieve messages \n')
        t_end = time.time() + (sock_timeout)
    
        while time.time() < t_end: 
            try:
                data, server = sock.recvfrom(1024)
            except socket.timeout:
                sys.stdout.write('timed out, no more responses \n')
                break
            else:
                sys.stdout.write(f'recieved {data.decode()} from {server} on {datetime.datetime.now().time()}\n')
                messages_recieved[num_of_messages].append(data.decode())
    
        sys.stdout.write('--------------------------------------\n')
        sock.settimeout(sock_timeout)
        num_of_messages += 1
    
    # Deleting Daemonset
    sys.stdout.write('Deleting recievers daemonset\n')
    delete_ds = requests.request('DELETE', f'{daemonsets_url}/reciever', headers=kube_request_headers, verify=verify_kube_ssl)
    while True:
        get_ds = requests.request('GET', f'{daemonsets_url}/reciever', headers=kube_request_headers, verify=verify_kube_ssl)
        if (json.loads(get_ds.content)["kind"] == "Status"):
            break
        time.sleep(2)
    
    # Creating vars for Splunk
    
    least_responses = 9000
    most_responses = 0
    responses_got = []
    for responses in messages_recieved:
        len_responses = len(responses)
        if (most_responses < len_responses):
            most_responses = len_responses
        if (least_responses > len_responses):
            least_responses = len_responses
        responses_got.append({"responses_amount":len_responses,"who_answered":responses})
    
    multicast_status = ''
    if (most_responses != 0):
        if (most_responses == least_responses):
            if (most_responses == desiredPodsNumber):
                multicast_status = 'Good'
            else:
                multicast_status = 'HalfGood'
        else:
            multicast_status = 'Inconsistent'
    else:
        multicast_status = 'Bad'
    
    sys.stdout.write('closing local socket\n')
    sock.close
    
    # Sending message to Splunk
    sys.stdout.write('Sending message to Splunk\n')
    
    splunk_token = os.environ['SPLUNK_TOKEN']
    splunk_url = os.environ['SPLUNK_API_URL']
    verify_splunk_ssl = os.environ['VERIFY_SPLUNK_SSL']
    
    request_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Splunk {splunk_token}"
    }
    
    body_params = {
        "event": {
            "event_type": "multicast_tester",
            "responses_got": responses_got,
            "desired_pods_amount": desiredPodsNumber,
            "pods_created" : numberPodsReady,
            "least_responses": least_responses,
            "most_responses": most_responses,
            "multicast_status": multicast_status,
            "cluster_name": kube_cluster_name
        }
    }
    
    r = requests.request('POST', splunk_url, headers=request_headers, json=body_params, verify=ast.literal_eval(verify_splunk_ssl))
    
    sys.stdout.write(f'Sending to splunk status: {json.loads(r.content)["text"]}\n')
    
    sys.stdout.write('Finished goodbye')
    
    exit()

if __name__ == "main":
    main()    