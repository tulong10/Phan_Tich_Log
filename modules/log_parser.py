import re 
from datetime import datetime
import streamlit as st
from typing import List, Tuple, Dict, Optional

LOG_PATTERN = re.compile(
    r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) '  
    r'- - '                                         
    r'\[(?P<time>[^\]]+)\] '                        
    r'"(?P<method>\w+) '                            
    r'(?P<path>[^\s]+) '                            
    r'HTTP/[0-9.]+" '                                
    r'(?P<status>\d{3}) '                           
    r'(?P<size>\d+|-)'                               
)

STATUS_MESSAGES ={
    200: "OK",
    201: "Created",
    204: "No Content",

    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",

    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",

    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

def determine_log_level (status_code : int) ->str:
  """
    Hàm dùng dể phân loại mức độ log dựa trên status code
  """
  if status_code <= 400:
    return "INFO"
  elif status_code < 500:
    return "WARNING"
  else:
    return "ERROR"
  

def determine_response_text(status_code: int) ->str:
  
  return STATUS_MESSAGES.get(status_code, f"HTTP {status_code}")

def validate_ip (ip_address: str) ->bool:
  try:
    parts = ip_address.split(".")

    if len(parts) !=4:
        return False
    for part in parts:
        num = int(part)
    if num <0 or num > 255:
        return False
    return True
  except ValueError:
    return False
  

