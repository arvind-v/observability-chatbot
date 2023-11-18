import boto3
import botocore
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


class OpenSearchHelper:

	EVENTS_INDEX_NAME = 'eks-kubernetes-events'
	CONTROL_PLANE_LOGS_INDEX_NAME = 'eks-control-plane-logs'
	POD_LOGS_INDEX_NAME = 'eks-pod-logs'

	MINUTES_TO_RETRIEVE = 15
	MAX_DOCUMENTS_TO_RETRIEVE = 1000
	#service = 'aoss'
	#region = 'us-west-2'
	#credentials = boto3.Session().get_credentials()
	#awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
	 #                  region, service, session_token=credentials.token)
	

	def __init__ (self, host, user, password, port = None):
		self.host = host
		self.user = user
		self.password = password
		self.port = 443 if not port else port
		
		self.client= OpenSearch(
			hosts=[{"host": self.host, "port": self.port}],
			http_auth=(user, password),
			use_ssl=True,
			verify_certs=True,
			connection_class=RequestsHttpConnection,
			timeout=300
		)

	# Retrieve last nn minutes of documents from the specified OpenSearch index
	# up to 'maxDocs' number of documents. Documents are returned with most
	# recent timestamp first.
	# The name of the field containing the timestamp is specified by 'timestampField'
	# since it varies depending on the index being retrieved. 
	def get_documents (self, index, timestampField, minutes, maxDocs=None):
		minutes = minutes if minutes else self.MINUTES_TO_RETRIEVE
		maxDocs = maxDocs if maxDocs else self.MAX_DOCUMENTS_TO_RETRIEVE
		query = {
			"query": {
				"range": {
				timestampField: {
					"gte": "now-{}m".format(minutes),
					"lte": "now",
					"format": "epoch_millis"
				}
			}
			},
			"sort": [{
				timestampField: {
					"order": "desc"
				}
			}]
		}
		response = self.client.search(index=index, body=query, size=maxDocs)
		return response["hits"]["hits"]

	# Retrieve last nn minutes of documents from OpenSearch index containing
	# control plane logs. Return only fields that are relevant to the LLM.
	# EKS Control Plane Logs entries include five types of records:
	# 	- API Server
	# 	- Authenticator
	# 	- Audit
	# 	- Controller Manager
	# 	- Scheduler
	#
	# kube-api-server messages are parseable as JSON, but other messages are not.
	# 
	def get_control_plane_logs (self, index=None, minutes=None, maxDocs=None):
		index = index if index else self.CONTROL_PLANE_LOGS_INDEX_NAME
		# Retrieve docs from OpenSearch 
		documents = self.get_documents(index=index, 
																   timestampField="@timestamp",
																 	 minutes=minutes, 
																	 maxDocs=maxDocs)
		logs = []
		for doc in documents:
			log_entry = {}
			log_entry["@timestamp"] = doc["_source"]["@timestamp"]
			log_entry["log_stream"] = doc["_source"]["@log_stream"]
			# Parse message as JSON if possible (i.e. from kube-api-server)
			try:
				log_entry["message"] = json.loads(doc["_source"]["@message"])
			except ValueError as e:
				log_entry["message"] = doc["_source"]["@message"]
			logs.append(log_entry)
		return logs
	
	# Retrieve last nn minutes of documents from OpenSearch index containing
	# Kubernetes events. Return only fields that are relevant to the LLM.
	# TODO: update this based on Kubernetes events structure 
	def get_events (self, index=None, minutes=None, maxDocs=None):
		index = index if index else self.EVENTS_INDEX_NAME
		# Retrieve docs from OpenSearch
		documents = self.get_documents(index=index, 
									   timestampField="lastTimestamp",
									 	 minutes=minutes, 
										 maxDocs=maxDocs)
		events = []
		for doc in documents:
			event = {}
			event["@timestamp"] = doc["_source"]["lastTimestamp"]
			event["type"] = doc["_source"]["type"]
			event["reason"] = doc["_source"]["reason"]
			event["namespace"] = doc["_source"]["metadata"]["namespace"]
			event["object_type"] = doc["_source"]["involvedObject"]["kind"]
			event["object_name"] = doc["_source"]["involvedObject"]["name"]
			event["message"] = doc["_source"]["message"]
			events.append(event)
		return events
	
	# Retrieve last nn minutes of documents from OpenSearch index containing 
	# pod logs. Return only fields that are relevant to the LLM.  
	# This includes: timestamp, log stream, pod name, namespace,
	# pod labels, container name, host, and log message.
	def get_pod_logs (self, index=None, minutes=None, maxDocs=None):
		if not minutes:
			minutes = self.MINUTES_TO_RETRIEVE
		if not index:
			index = self.POD_LOGS_INDEX_NAME
		documents = self.get_documents(index=index, 
									   timestampField="@timestamp",
									 	 minutes=minutes, 
										 maxDocs=maxDocs)
		logs = []
		for doc in documents:
			log_entry = {}
			log_entry["@timestamp"] = doc["_source"]["@timestamp"]
			log_entry["log_stream"] = doc["_source"]["stream"]
			log_entry["pod_name"] = doc["_source"]["kubernetes"]["pod_name"]
			log_entry["namespace"] = doc["_source"]["kubernetes"]["namespace_name"]        
			log_entry["pod_labels"] = doc["_source"]["kubernetes"]["labels"]        
			log_entry["container_name"] = doc["_source"]["kubernetes"]["pod_name"]        
			log_entry["host"] = doc["_source"]["kubernetes"]["host"]
			log_entry["message"] = doc["_source"]["log"]
			logs.append(log_entry)
		return logs
