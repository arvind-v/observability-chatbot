import boto3

class ParameterStoreHelper:
  
  # Requires base path where parameters are stored 
  # in SSM parameter store
  def __init__ (self, basePath):
    self.ssm = boto3.client('ssm')
    self.basePath = basePath
    self.host = self.getParameter('host')
    self.user = self.getParameter('user', decrypt=True)
    self.password = self.getParameter('password', decrypt=True)

  # Get parameter from SSM parameter store
  def getParameter (self, parameterName, decrypt=False):
    return self.ssm.get_parameter(
      Name=self.basePath + '/' + parameterName,
      WithDecryption=decrypt
    )['Parameter']['Value']
  
  # Get host
  def getHost (self):
    return self.getParameter('host')

  # Get user
  def getUser (self):
    return self.getParameter('user', decrypt=True)
  
  # Get password
  def getPassword (self):
    return self.getParameter('password', decrypt=True)
  
