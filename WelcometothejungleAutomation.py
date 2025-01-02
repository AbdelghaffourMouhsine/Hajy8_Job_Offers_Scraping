from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
import time , random
import os, re, json, copy
import zipfile
from bs4 import BeautifulSoup

# from contact_links_classification.ContactLinkModel import ContactLinkModel
# from OpenAI_API import ContactOpenAIScraping
# from pageProcessing import PageProcessing
# from sentenceProcessing import SentenceProcessing

class WelcometothejungleAutomation:
    
    def __init__(self, url=None, proxy=None, with_selenium_grid=False):
        self.url = url
        self.proxy = proxy
        if self.proxy :
            self.PROXY_HOST = proxy["PROXY_HOST"] # rotating proxy or host
            self.PROXY_PORT = proxy["PROXY_PORT"] # port
            self.PROXY_USER = proxy["PROXY_USER"] # username
            self.PROXY_PASS = proxy["PROXY_PASS"] # password
            self.options = self.get_options_for_proxy()
        else:
            self.options = webdriver.ChromeOptions()

        # self.options.add_argument("--headless")
        
        self.with_selenium_grid = with_selenium_grid
        if self.with_selenium_grid:
            # IP address and port and server of the Selenium hub and browser options
            self.HUB_HOST = "localhost"
            self.HUB_PORT = 4444
            self.server = f"http://{self.HUB_HOST}:{self.HUB_PORT}/wd/hub"
            self.driver = webdriver.Remote(command_executor=self.server, options=self.options)
        else:
            self.driver = webdriver.Chrome(options=self.options)

        self.driver.maximize_window()

        self.sentenceProcessing = None
        self.pageProcessing = None
        self.contactOpenAIScraping = None
        self.contact_link_classifier = None
        self.phones = []
        self.emails = []
        self.addresses = []
        
    def init_classes_for_contact_scraping(self):
        self.contact_link_classifier = ContactLinkModel()
        self.contact_link_classifier.load_from_local(model_path='./contact_links_classification/Models/model_0/model_contact_40_maxlen_10_epochs')
        self.sentenceProcessing = SentenceProcessing(max_words_before_phone_number_or_email=10)
        self.pageProcessing = PageProcessing()
        self.contactOpenAIScraping = ContactOpenAIScraping()
        
    def quit_driver(self):
        self.driver.quit()

    def get_options_for_proxy(self):
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """
        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (self.PROXY_HOST, self.PROXY_PORT, self.PROXY_USER, self.PROXY_PASS)
        
        def get_chrome_options(use_proxy=True, user_agent=None):
            chrome_options = webdriver.ChromeOptions()
            if use_proxy:
                pluginfile = 'proxy_auth_plugin.zip'
        
                with zipfile.ZipFile(pluginfile, 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", background_js)
                    
                chrome_options.add_extension(pluginfile)
                
            if user_agent:
                chrome_options.add_argument('--user-agent=%s' % user_agent)
            
            return chrome_options
        return get_chrome_options()
        
    def click_elem(self, click_elem):
        t=1
        check = 0
        i = 0
        while not check and i<5:
            try:
                click_elem.click()
                time.sleep(t)     ######
                check = 1
                return True
            except Exception as e:
                check = 0
            i += 1
        return False

    def get_element(self, path_to_elem, from_elem=None, group=False, innerTextLower=None, containsText=None):
        i = 0
        while i<5:
            try:
                if not from_elem :
                    from_elem = self.driver
                
                if not group:
                    elem = from_elem.find_element(By.XPATH, path_to_elem)
                    
                else : # group is True
                    elems = from_elem.find_elements(By.XPATH, path_to_elem)
                    elem = elems
                    if innerTextLower :
                        for e in elems:
                            if str(e.get_attribute("innerText")).strip().lower() == str(innerTextLower).strip().lower():
                                elem = e
                                break
                                
                    if innerTextLower and type(elem) == list:
                        return {"status": False, "data": f'cannot find an element with this lower innerText : {innerTextLower}' }
                    
                return {"status": True, "data":elem }
                        
            except Exception as e:
                i += 1
                if i == 5:
                    return {"status": False, "data":str(e) }

    ########################################################################################################
    #---------------------------------- get welcometothejungle authentication ----------------------------------------
    ########################################################################################################
    def get_authentication(self, email = '', pwd = ''):
        
        url = 'https://www.welcometothejungle.com/fr/'
        self.driver.get(url)
        time.sleep(2)
        i = 0
        while self.driver.current_url != 'https://www.welcometothejungle.com/fr/me/dashboard' and i<3 :
            close_button = self.get_element('//div[@aria-label="language selector modal"]/div/header/button[@title="Close"]')
            if close_button["status"]:
                close_button = close_button["data"]
                self.click_elem(close_button)
            else:
                print({"status": False, "data":close_button["data"] })
            time.sleep(2)
            
            login_button = self.get_element('//*[@data-testid="not-logged-visible-login-button"]')
            if login_button["status"]:
                login_button = login_button["data"]
                self.click_elem(login_button)
            else:
                print({"status": False, "data":login_button["data"] })
            time.sleep(2)
    
            input_username = self.get_element('//*[@id="email_login"]')
            if input_username["status"]:
                input_username = input_username["data"]
                input_username.send_keys(email)
                input_username.send_keys(Keys.ENTER)
            else:
                print({"status": False, "data":input_username["data"] })
            time.sleep(2)
        
            input_password = self.get_element('//*[@id="password"]')
            if input_password["status"]:
                input_password = input_password["data"]
                input_password.send_keys(pwd)
                input_password.send_keys(Keys.ENTER)
            else:
                print({"status": False, "data":input_password["data"] })
            time.sleep(2)
            
            close_button = self.get_element('//form[@data-testid="finalize-profile-modal"]/header/button[@title="Close"]')
            if close_button["status"]:
                close_button = close_button["data"]
                self.click_elem(close_button)
            else:
                print({"status": False, "data":close_button["data"] })
            time.sleep(2)
            
            acceptAllCookies_button = self.get_element('//*[@id="axeptio_btn_acceptAll"]')
            if acceptAllCookies_button["status"]:
                acceptAllCookies_button = acceptAllCookies_button["data"]
                self.click_elem(acceptAllCookies_button)
            else:
                print({"status": False, "data":acceptAllCookies_button["data"] })
            time.sleep(2)
            i = i+1
            
        print('WelcometothejungleAutomation --> yes')
        time.sleep(5)