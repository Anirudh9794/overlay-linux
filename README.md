# overlay-linux
Linux networking project
## Requirements
* python 3
* ansible-playbook
## Setup
1. Install python 3.6+
2. Install pip
3. Install libvirt-python using pip
4. Create a virtual environment: `python3 -m venv venv`
5. Activate virtual environment: `source ./venv/bin/activate`
6. Installing requirements: `pip install -r requirements.txt`
7. Installing modules: `python setup.py install`
## Starting the Northbound REST server
Need to provide hostname where provider will run. Ex is:
``` bash
python3 overlay.py
```
## Making a request to the REST server
``` bash
curl -X POST 127.0.0.1:8081/vpc -d '{"vpcName":"vpc101","host":"Host1","customerName":"customer1"}' -H 'Content-Type: application/json'
```
