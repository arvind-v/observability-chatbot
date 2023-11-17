import boto3
import json
from opensearchpy import OpenSearch

# Retrieve OpenSeearch coordinates from SSM Parameter Store
def get_opensearch_params(eks_cluster_name):
    ssm = boto3.client("ssm")
    base_path = '/eksworkshop/' + eks_cluster_name + '/opensearch'
    print (base_path)

    opensearch_host = ssm.get_parameter(Name=base_path + '/host')
    opensearch_user = ssm.get_parameter(Name=base_path + '/user', WithDecryption=True)
    opensearch_password = ssm.get_parameter(Name=base_path + '/password', WithDecryption=True)
    return opensearch_host, opensearch_user, opensearch_password

# Create OpenSearch client
def get_opensearch_client(host, user, password, port = 443):
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(user, password),
        use_ssl=True,
        verify_certs=True,
        connection_class=None,
    )
    return client

# Retrieve last nn minutes of documents from the 'eks-pod-logs' OpenSearch index
def get_documents (client, index, minutes):
    query = {
        "query": {
            "range": {
                "@timestamp": {
                    "gte": "now-{}m".format(minutes),
                    "lte": "now",
                    "format": "epoch_millis"
                }
            }
        },
        "sort": [{
            "@timestamp": {
                "order": "desc"
            }
        }]
    }
    response = client.search(index=index, body=query, size = 100)
    return response["hits"]["hits"]

# Retrieve last nn minutes of documents from the 'eks-pod-logs' OpenSearch index
def get_logs (client, index='eks-pod-logs', minutes=15):
    documents = get_documents(client, index, minutes)
    logs = []
    for document in documents:
        log_entry = {}
        log_entry["@timestamp"] = document["_source"]["@timestamp"]
        log_entry["log_stream"] = document["_source"]["stream"]
        log_entry["pod_name"] = document["_source"]["kubernetes"]["pod_name"]
        log_entry["namespace"] = document["_source"]["kubernetes"]["namespace_name"]        
        log_entry["pod_labels"] = document["_source"]["kubernetes"]["labels"]        
        log_entry["container_name"] = document["_source"]["kubernetes"]["pod_name"]        
        log_entry["host"] = document["_source"]["kubernetes"]["host"]
        log_entry["log_message"] = document["_source"]["log"]

        logs.append(log_entry)
    return logs

# Invoke LLM
def invokeLLM (question, logs):
    # Setup Bedrock client
    bedrock = boto3.client('bedrock-runtime', 'us-west-2', endpoint_url='https://bedrock-runtime.us-west-2.amazonaws.com')
    # configure model specifics such as specific model
    modelId = 'anthropic.claude-v2'
    accept = 'application/json'
    contentType = 'application/json'
    # prompt that is passed into the LLM with the Kendra Retrieval context and question
    # TODO: FEEL FREE TO EDIT THIS PROMPT TO CATER TO YOUR USE CASE
    prompt_data = f"""\n\nHuman:    
Answer the following question to the best of your ability based on the context provided.
Provide an answer and provide sources and the source link to where the relevant information can be found. Include this at the end of the response
Do not include information that is not relevant to the question.
Only provide information based on the context provided, and do not make assumptions
Only Provide the source if relevant information came from that source in your answer
Use the provided examples as reference
###
Question: {question}

Context: {logs}

###

\n\nAssistant:

"""
    # body of data with parameters that is passed into the bedrock invoke model request
    # TODO: TUNE THESE PARAMETERS AS YOU SEE FIT
    body = json.dumps({"prompt": prompt_data,
                       "max_tokens_to_sample": 8191,
                       "temperature": 0,
                       "top_k": 250,
                       "top_p": 0.5,
                       "stop_sequences": []
                       })
    # Invoking the bedrock model with your specifications
    response = bedrock.invoke_model(body=body,
                                    modelId=modelId,
                                    accept=accept,
                                    contentType=contentType)
    # the body of the response that was generated
    response_body = json.loads(response.get('body').read())
    # retrieving the specific completion field, where you answer will be
    answer = response_body.get('completion')
    # returning the answer as a final result, which ultimately gets returned to the end user
    return answer
    




# Warning - works only if prepare-environment has been run 
# Therefore, need a way to connect to OpenSearch ONLY after the prepare-environment has been run
#h, u, p = get_opensearch_params('eks-workshop-1026')
#print (h)
#print (u)
#print (p)


c = get_opensearch_client (host = "search-opensearch-for-kube-56harttmehr4x3jp6zonaou3pq.us-west-2.es.amazonaws.com",
                       user = 'admin',
                       password = '8NXppvcefJyMkshHD*1')
#docs = get_documents (client=c,index = 'eks-pod-logs', minutes='999999')

docs = get_logs (client=c,index = 'eks-pod-logs', minutes='999999')
print ('****')
# number of documents
print (len(docs))
# print first 10 docs
print ('****')
for i in range(10):
  print (docs[i])
print ('****')

answer = invokeLLM (question = 'Summarize log messages provided in the context', logs = docs)

print ('****')
print (answer)

#with open("logs.json", "w") as outfile:
#    json.dump(docs, outfile)


