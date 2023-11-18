# Use Langchain to interface with Bedrock

#from langchain.chat_models import BedrockChat
#from langchain.schema import HumanMessage
#from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from opensearch_helper import OpenSearchHelper
from param_store_helper import ParameterStoreHelper
from bedrock_helper import BedrockHelper
import json
import streamlit as st

st.title("💬 EKS Assistant")
st.caption("🚀 A streamlit chatbot powered by Amazon Bedrock")


ps = ParameterStoreHelper('/eksworkshop/eks-workshop-1026/opensearch')
opensearch = OpenSearchHelper (host = ps.host,
                               user = ps.user,
                               password = ps.password)
#events = opensearch.get_events(minutes=1000)
#cpl = opensearch.get_control_plane_logs()
pl = opensearch.get_pod_logs(minutes=1000)




if "input" not in st.session_state:
    st.session_state["input"] = ""
if "temp" not in st.session_state:
    st.session_state["temp"] = ""
    
def clear_text():
    st.session_state["temp"] = st.session_state["input"]
    st.session_state["input"] = ""
    
    
# Define function to get user input
def get_text():
    """
    Get the user input text.

    Returns:
        (str): The text entered by the user
    """
    input_text = st.text_input("You: ", st.session_state["input"], key="input", 
                            placeholder="Your AI assistant here! How may i help you?", 
                            on_change=clear_text,    
                            label_visibility='hidden')
    input_text = st.session_state["temp"]
    return input_text


# Get the user input
user_input = get_text()


if user_input != "":
    bedrockClient = BedrockHelper(user_input) 
#response = bedrockClient.invokeBedrockChat()
    response = bedrockClient.invokeLLM("eks-pod-logs")
    response
#st.write(response)
