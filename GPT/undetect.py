import undetected_chromedriver as uc
import time
from selenium.webdriver.common.by import By
import os
from pyChatGPT import ChatGPT
from dotenv import dotenv_values
env_vars = dotenv_values(".env")
current_directory = os.getcwd()

email = env_vars['EMAIL']
password = env_vars['PASSWORD']

api = ChatGPT(auth_type='openai', 
              email=email, 
              password=password, 
              conversation_id='266d06e1-6263-4642-a198-14057c32dbde',
              login_cookies_path=current_directory+'/cookies',
            #   chrome_args=['--headless']
              )

while True:
    message = input("enter message: ")
    resp = api.send_message(message)
    print(resp['message'])