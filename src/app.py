# Use Langchain to interface with Bedrock

from langchain.chat_models import BedrockChat
from langchain.schema import HumanMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from opensearch_helper import OpenSearchHelper
from param_store_helper import ParameterStoreHelper
import json

"""
Outline for interacting with Bedrock
  - Retrieve data from OpenSearch. This will be used for answering questions
  - Split the OpenSearch data into chunks
  - 


"""


ps = ParameterStoreHelper('/eksworkshop/eks-workshop-1026/opensearch')
opensearch = OpenSearchHelper (host = ps.host,
                               user = ps.user,
                               password = ps.password)
events = opensearch.get_events(minutes=1000)
cpl = opensearch.get_control_plane_logs()
pl = opensearch.get_pod_logs(minutes=1000)

#print (json.dumps(events[0], indent=2))
#print (json.dumps(cpl[0], indent=2))
#print (json.dumps(pl[0], indent=2))



try: 
  chat = BedrockChat(
      model_id="anthropic.claude-v2",
      streaming=True,
      callbacks=[StreamingStdOutCallbackHandler()],
      model_kwargs={
        #"maxTokenCount": 8191,
        #"stopSequences": [],
        #"topK": 250,
        #"topP": 0.5,
        "temperature": 0.0
        },
  )

  messages = [
      HumanMessage(
          content="Translate this sentence from English to French. I love programming."
      )
  ]


  chat(messages)
except Exception as e:
  print(e)
