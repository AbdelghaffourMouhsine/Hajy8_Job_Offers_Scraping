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

class LinkedinAutomation:
    
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
    #---------------------------------- get linkedin authentication ----------------------------------------
    ########################################################################################################
    def get_linkedin_authentication(self, email = '', pwd = ''):
        
        url = 'https://www.linkedin.com/login/fr?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'
        self.driver.get(url)
        time.sleep(2)
        
        input_username = self.get_element('//*[@id="username"]')
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

        print('linkedin_authentication --> yes')
        time.sleep(20)
    ########################################################################################################
    #-------------------------------------------- scroll_down ----------------------------------------------
    ########################################################################################################
    def scroll_down(self, button_path_to_show_more_results=None, button_text_to_show_more_results=None, bottom_distance=0, max_scrolling=-1):
        # bottom_distance => distance between the bottom of the page and the More results button
        # self.scroll_down(button_path_to_show_more_results='//button', button_text_to_show_more_results='afficher plus de résultats')
    
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        second_check = False
        i=0
        while True and (max_scrolling==-1 or i < max_scrolling):
            # Scroll down to bottom
            self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight  - {bottom_distance});")
            # Calculate new scroll height and compare with total scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            # Wait to load page
            time.sleep(random.uniform(2, 4))
            if new_height == last_height:
                time.sleep(random.uniform(1.5,2.5))
                temp = False
                if not temp:
                    if button_text_to_show_more_results in str(self.get_element('//body')['data'].get_attribute('innerText')).lower():
                        show_more_results_button = self.get_element(button_path_to_show_more_results, group=True, innerTextLower=str(button_text_to_show_more_results).strip().lower())
                        if show_more_results_button["status"]:
                            show_more_results_button = show_more_results_button["data"]
                            self.click_elem(show_more_results_button)
                            temp = True
                            print("yeeeees : 'show_more_results_button' is clecked.......")
                            # Wait to load page
                            time.sleep(random.uniform(2, 4))
                if second_check and not temp:
                    break
                    
                if not temp:
                    second_check = True
                
            last_height = new_height
            i+=1
    ########################################################################################################
    #------- extract linkedin profiles that work at a company from the company linkedin profile url --------
    ########################################################################################################
    def extract_profiles_from_company_linkedin_profile_url(self, company_linkedin_url):
        company_linkedin_url = str(company_linkedin_url)
        
        try:
            if 'company' in company_linkedin_url :
            
                a_personnes_link = f'https://www.linkedin.com/company/{company_linkedin_url.split("/company/")[1].split("/")[0]}/people'
                                
                if a_personnes_link:
                    self.driver.get(a_personnes_link)
                    time.sleep(random.uniform(2,3))

                    self.scroll_down(button_path_to_show_more_results='//button', button_text_to_show_more_results='afficher plus de résultats')

                # /html/body/div[5]/div[3]/div/div[2]/div/div[2]/main/div[2]/div/div/div[2]/div/div[1]/ul/li
                # //li[contains(@class,"org-people-profile-card__profile-card-spacing")]
                # //div[@class="artdeco-card org-people-profile-card__card-spacing org-people__card-margin-bottom"]/div/div/ul/li
                
                personnes_li_s = self.get_element('//li[contains(@class,"org-people-profile-card__profile-card-spacing")]', group=True)
                    
                profiles = []
                if personnes_li_s["status"]:
                    personnes_li_s = personnes_li_s["data"]
                    # print(f'le nombre de personnes avant extract est: {len(personnes_li_s)}')
                    for li in personnes_li_s:
                        profile = self.get_personne_profile_from_li(li)
                        if profile["status"]:
                            # print(profile["data"])
                            profiles.append(profile["data"])
                        # else:
                        #     print(f'profile : {profile}')
                    # print(f'le nombre de personnes apres extract est : {len(profiles)}')
                else:
                    print({"status": False, "data": personnes_li_s["data"] })
    
                return {"status": True, "data": profiles }

            else:
                return {"status": False, "data": 'not valid company_linkedin_url'}
                
        except Exception as e:
            print(f'ERROOOOR: ({company_linkedin_url},{type(company_linkedin_url)}) {e}')
            return {"status": False, "data": str(e) }

    #/div/section/div/div/div[2]/div[1]/a
    
    def get_personne_profile_from_li(self, personne_li):
        personne_dic = {}
        a_profile_url = self.get_element('div/section/div/div/div[2]/div[1]/a', from_elem=personne_li)
        if a_profile_url["status"]:
            a_profile_url = a_profile_url["data"]
            personne_dic['profile_url'] = a_profile_url.get_attribute('href')
            personne_dic['profile_name'] = a_profile_url.get_attribute("innerText")
        else:
            # print(personne_li.get_attribute('innerText'))
            return {"status": False, "data": a_profile_url["data"] }

        div_profile_description = self.get_element('div/section/div/div/div[2]/div[@class="artdeco-entity-lockup__subtitle ember-view"]', from_elem=personne_li)
        if div_profile_description["status"]:
            div_profile_description = div_profile_description["data"]
            personne_dic['profile_description'] = div_profile_description.get_attribute("innerText")
            
        else:
            print({"status": False, "data": div_profile_description["data"] })
            
        return {"status": True, "data": personne_dic }

    ########################################################################################################
    #------------------------- get company linkedin url from company web site url --------------------------
    ########################################################################################################
    def get_company_linkedin_url_from_company_web_site_url(self, company_web_site_url):
        company_web_site_url = str(company_web_site_url).strip()
        try:
            if company_web_site_url:
                self.driver.get(company_web_site_url)
                time.sleep(0.5)
                
                html_content = self.driver.page_source
                # Analyser le contenu HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Rechercher les liens LinkedIn dans les balises <a>
                linkedin_links = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    # Vérifier si l'URL contient 'linkedin.com'
                    if 'linkedin.com' in href and 'company' in href:
                        linkedin_links.append(href)
                
                # Afficher les liens LinkedIn extraits
                print(linkedin_links)
                
                company_linkedin_url = None
                if linkedin_links:
                    company_linkedin_url = linkedin_links[0]

                return {"status": True, "data": company_linkedin_url}
            else:
                return {"status": False, "data": None }
        except Exception as e:
            print(f'ERROOOR: {e}')
            return {"status": False, "data": str(e)}
            
    ############################################################################################################
    #----------------------------- linkedin url from GOOGLE based on company_name ------------------------------
    ############################################################################################################
    def get_google_page(self):
        self.driver.get('https://www.google.com')
        time.sleep(random.uniform(0.5, 2))
        
        input_search = self.get_element('//*[@id="APjFqb"]')
        if input_search["status"]:
            input_search = input_search["data"]
            input_search.send_keys('some keys for get results')
            input_search.send_keys(Keys.ENTER)
        else:
            print({"status": False, "data":input_search["data"] })
        time.sleep(3)
        
    def get_linkedin_url_from_company_name(self, company_name):
        company_name = str(company_name)
        try:
            input_search = self.get_element('//*[@id="APjFqb"]')
            if input_search["status"]:
                input_search = input_search["data"]
                # Effacer le champ de saisie avant d'ajouter une nouvelle valeur
                input_search.clear()  # Supprime le contenu existant de l'input
                keywords = company_name.strip() + ' linkedin company'
                input_search.send_keys(keywords)  # Ajouter la nouvelle valeur
                time.sleep(random.uniform(0.5, 2))
                input_search.send_keys(Keys.ENTER)  # Envoyer le formulaire ou valider la recherch
            else:
                print({"status": False, "data":input_search["data"] })
            time.sleep(random.uniform(1,1.5))
            
            a_linkedin = self.get_element('//a[@jsname="UWckNb"]')
            if a_linkedin["status"]:
                a_linkedin = a_linkedin["data"]
                linkedin_url = a_linkedin.get_attribute('href')
                return {"status": True, "data": linkedin_url }
                
            else:
                print({"status": False, "data": a_linkedin["data"] })
                return {"status": False, "data": a_linkedin["data"]}
            
        except Exception as e:
            print(f'ERROOOR: {e}')
            return {"status": False, "data": str(e) }

    ########################################################################################################
    #--------------------- extract company information from the company's linkedin about page --------------
    ########################################################################################################
    def extract_company_info_from_company_linkedin_profile_url(self, company_linkedin_url):
        company_linkedin_url = str(company_linkedin_url)
        try:
            if 'company' in company_linkedin_url :
            
                a_personnes_link = f'https://www.linkedin.com/company/{company_linkedin_url.split("/company/")[1].split("/")[0]}/about/'
                                
                self.driver.get(a_personnes_link)
                time.sleep(random.uniform(2,3))
                dict = {}
                size_elem = self.get_element('//a[contains(@class, "org-top-card-summary-info-list__info-item")]/span')
                if size_elem['status']:
                    size_elem = size_elem['data']
                    dict['company_size'] = [size_elem.get_attribute('innerText').replace('\xa0', ' ')]
                else:
                    print(size_elem['data'])

                # /html/body/div[6]/div[3]/div/div[2]/div/div[2]/main/div[2]/div/div/div/div[1]/section/dl
                # class="artdeco-card org-page-details-module__card-spacing artdeco-card org-about-module__margin-bottom"
                about_infos = self.get_element('//section[contains(@class, "org-page-details-module__card-spacing")]/dl/*', group=True)
                if about_infos['status']:
                    about_infos = about_infos['data']
                    #about_infos = about_infos.get_attribute('innerText')
                    last_dt = ''
                    for about_info_elem in about_infos:
                        if about_info_elem.tag_name == 'dt':
                            last_dt = about_info_elem.get_attribute('innerText').strip().lower()
                            dict[last_dt] = []
                            
                        if about_info_elem.tag_name == 'dd':
                            dict[last_dt].append(about_info_elem.get_attribute('innerText').strip().lower().replace('\u202f', ' ').replace('\xa0',' '))
                else:
                    print(about_infos['data'])

                about_infos = self.get_element('//section[contains(@class, "org-page-details-module__card-spacing")]/*', group=True)
                if about_infos['status']:
                    about_infos = about_infos['data']
                    for about_info_elem in about_infos:
                        if about_info_elem.tag_name == 'h2':
                            last_dt = about_info_elem.get_attribute('innerText').strip().lower()
                            dict[last_dt] = []
                            
                        if about_info_elem.tag_name == 'p':
                            dict[last_dt].append(about_info_elem.get_attribute('innerText').strip().lower().replace('\u202f', ' ').replace('\xa0',' '))
                            
            else:
                return {"status": False, "data": 'not valid company_linkedin_url'}
            return {"status": True, "data": dict}
        except Exception as e:
            print(f'ERROOOOR: ( {company_linkedin_url} ) {e}')
            return {"status": False, "data": str(e) }
    ########################################################################################################
    #--------------------- extract founder and manager profiles based on keywords --------------------------
    ########################################################################################################
    def str_to_json(self, json_string):
        def clean_invalid_escapes(json_string):
            # Supprime les séquences d'échappement invalides
            cleaned_string = re.sub(r'\\U[0-9a-fA-F]{8}', '', json_string)
            cleaned_string = re.sub(r'\\x[0-9a-fA-F]{2}', '', cleaned_string)
            return cleaned_string
        json_string = json_string.replace('"', "'")
        json_string = json_string.replace("{'", '{"')
        json_string = json_string.replace("', '", '", "')
        json_string = json_string.replace("\", '", '", "')
        json_string = json_string.replace("', \"", '", "')
        json_string = json_string.replace("': '", '": "')
        json_string = json_string.replace("': \"", '": "')
        json_string = json_string.replace("\": '", '": "')
        json_string = json_string.replace("'}", '"}')
        json_string = json_string.replace("'", "\'")
        json_string = json_string.replace("\\'", "\'")
        json_string = json_string.replace("': ['", '": ["').replace("'], '", '"], "').replace("']}", '"]}').replace("': [", '": [')
        json_string = clean_invalid_escapes(json_string)
        json_object = json.loads(json_string)
        return json_object
        
    def extract_founder_and_manager_profiles_based_on_keywords(self, dict, for_commercial=False):        
        profiles_column = str(dict['profiles']).strip()
        company_name = str(dict['company_name']).strip()
            
        try:
            if company_name : # == "Groupe SYD" :
                print(f"{'@'*50}  {company_name}  {'@'*50}")
                    
                if profiles_column not in ["nan", 'none', 'null', '[]', ""]:
                    profiles = []
                    for i, profile in enumerate('}&&||&&'.join(profiles_column[1:-1].split('},')).split('&&||&&')):
                        # print(f'{i} : {profile}')
                        
                        profile = self.str_to_json(profile)
                        # print(f'{i} : {profile["profile_description"]}')
                        # print(f'*'*150)

                        profiles.append(profile)

                    #valid_profiles = profiles
                    valid_profiles = self.get_valid_profiles_from_profiles(profiles, for_commercial)

                    # print(f'='*150)
                    # for i in valid_profiles:
                    #     print(f'{i.founder_name} : {i.founder_description}')
                        
                else:
                    return {"status": False, "data": "profiles_column in ['nan', 'none', 'null', '[]', '']" }

            return {"status": True, "data": valid_profiles }
                
        except Exception as e:
            print(f"Errooooor at {company_name}")
            return {"status": False, "data": e.args[0]}

    def get_valid_profiles_from_profiles(self, profiles, for_commercial, use_OpenAI_api = False):
        profiles_for_openAI = []
        valid_profiles = []
        
        for profile in profiles:
            result=self.is_founder_director(profile["profile_description"], for_commercial)
            if result['response']:
                print(f'+++ valid profil : {profile["profile_description"]}')
                valid_profiles.append(profile)
            else:
                profiles_for_openAI.append(profile)
    
        profiles = profiles_for_openAI
        step = 50
        founder_profiles = []
        
        if use_OpenAI_api :
            for i in range(0,len(profiles),step):
                chunk = [ f'{profile["person_name"]}, {profile["profile_description"]}' for profile in profiles[i:i+step]]
        
                result = self.foundersOpenAIClassification.predict(chunk)
                # display(chunk)
                # print(f'*'*150)
                # print('Founder profiles:')
                
                for name, value in result['content'].items():
                    try:
                        if value:
                            profile = [profile for profile in profiles if profile['person_name'].strip() == name.strip()][0]
                            founder_profiles.append(profile)
                            print(f'--- valid profil : {profile["profile_description"]}')
                            # display(profile)
                            # print(f'*'*150)
                    except Exception as e:
                        print(f'===> error at founder name : {name}')
                        ExceptionStorage(self.item, f'===> error at founder name : {name}')
                #print(f'$'*150)
    
        final_valid_profiles = valid_profiles + founder_profiles
        return final_valid_profiles

    def is_founder_director(self, description, for_commercial):
        if not for_commercial:
            keywords = [
                "general director", "directeur général", "directrice générale",
                "commercial director", "directeur commercial", "directrice commercial", "DR commercial", "head of sales",
                " CEO", " PDG", " CFO", "CEO ", "PDG ", "CFO ",
                "president", "président", "présidente",
                "founder", "fondateur", "fondatrice",
                "co-founder", "Co-fondatrice", "Co-fondateur",
                " CTO", "CTO ",
                "Chief", "Chef d'entreprise"
                "HR director", "DRH", "directeur RH", "directrice RH", "DHR",
                "partner", "associé", "associée",
                "owner",
                "Investor", "investeur", "Entrepreneur"
            ]
    
            keywords_1 = ["CEO", "PDG", "CFO","CTO"]
        else:
            keywords = [
                "general director", "directeur général", "directrice générale",
                "commercial director", "directeur commercial", "directrice commercial", "DR commercial", "head of sales", "chef des ventes",
                "sales director", "directeur des ventes",
                " CEO", " PDG", "CEO ", "PDG ",
                "president", "président", "présidente",
                "founder", "fondateur", "fondatrice",
                "co-founder", "Co-fondatrice", "Co-fondateur",
                "Chef d'entreprise"
                "partner", "associé", "associée",
                "owner",
                "Investor", "investeur", "Entrepreneur"
            ]
    
            keywords_1 = ["CEO", "PDG"]
            
        # Exclude "product owner" explicitly
        if "product owner" in str(description).lower():
            return {"response": False}
    
        # Check if any keyword is in the description
        for keyword in keywords:
            if keyword.lower() in str(description).lower():
                return {"response": True}
                
        # Check if any keyword is in the description without lower()
        for keyword in keywords_1:
            if keyword in str(description):
                return {"response": True}
                
        return {"response": False}

    ########################################################################################################
    #---------------------- extract company linkedin url from web site url ---------------------------------
    ########################################################################################################
    def extract_company_linkedin_url_from_startup_web_site(self, web_site_url):
        web_site_url = str(web_site_url)
        try:
            linkedin_url = None
            if web_site_url != 'nan':
                self.driver.get(web_site_url)
                time.sleep(0.5)
                
                html_content = self.driver.page_source
                # Analyser le contenu HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Rechercher les liens LinkedIn dans les balises <a>
                linkedin_links = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    # Vérifier si l'URL contient 'linkedin.com'
                    if 'linkedin.com' in href and 'company' in href:
                        linkedin_links.append(href)
                
                # Afficher les liens LinkedIn extraits
                print(linkedin_links)
                if linkedin_links:
                    linkedin_url = linkedin_links[0]

                return {"status": True, "data": linkedin_url }
            else:
                return {"status": True, "data": linkedin_url }
        except Exception as e:
            print(f'ERROOOR: {e}')
            return {"status": False, "data": str(e) }
        finally:
            self.driver.quit()
    ########################################################################################################
    #------------------------ extract contact information from website URL -----------------------------
    ########################################################################################################
    def extract_contact_information_from_website_url(self, web_site_url):
        self.addresses = []
        self.emails = []
        self.phones = []
        try:
            if not self.contact_link_classifier:
                self.init_classes_for_contact_scraping()
                
            if str(web_site_url.strip()) != 'nan':
                if 'http' not in web_site_url:
                    web_site_url = f'https://{web_site_url.strip()}'
                    
                self.driver.get(web_site_url)
                time.sleep(0.5)
                self.extract_contact_inf_from_current_page()
                html_source = self.driver.page_source
                contact_links = list(set(self.contact_link_classifier.get_contact_links(html_source)))
                # print('contact_links : ',contact_links)
                visited_contact_links = []
                for index, contact_link in enumerate(contact_links):
                    if index != 0:
                        self.driver.get(web_site_url)
                        time.sleep(0.5)
                        
                    a_elem = self.get_element(f'//a[@href="{contact_link[0]}"]')
                    # print(a_elem)
                    if a_elem["status"]:
                        a_elem = a_elem["data"]
                        a_href = a_elem.get_attribute('href')
                        if a_href not in visited_contact_links:
                            first_url = str(self.driver.current_url)
                            self.click_elem(a_elem)
                            time.sleep(0.5)
                            current_url = str(self.driver.current_url)
                            if first_url != current_url:
                                visited_contact_links.append(current_url)
                                print(current_url)
                                self.extract_contact_inf_from_current_page()
                            else:
                                try:
                                    if a_href not in visited_contact_links:
                                        if 'http' in a_href:
                                            visited_contact_links.append(a_href)
                                            print(a_href)
                                            self.driver.get(a_href)
                                            time.sleep(0.5)
                                            self.extract_contact_inf_from_current_page()
                                        else:
                                            built_contact_link = '/'.join((web_site_url.split('/'))[:3]) + a_href
                                            if built_contact_link not in visited_contact_links:
                                                visited_contact_links.append(a_href)
                                                print(built_contact_link)
                                                self.driver.get(built_contact_link)
                                                time.sleep(0.5)
                                                self.extract_contact_inf_from_current_page()
                                except Exception as e:
                                    print('cannot click on the contact page link ****************************************************************************************')
                    else:
                        print(a_elem)
        
                self.phones = list(set(self.phones))
                self.emails = list(set(self.emails))
                self.addresses = list(set(self.addresses))
                
                for fake_email in ['info@company.com', 'support@company.com','contact@company.com', 'sales@company.com','contact@example.com', 'support@example.com', 'info@example.com', 'sales@example.com']:
                    if fake_email in self.emails:
                        self.emails.remove(fake_email)
                        
                return {"status": True, "data": {"phones":self.phones, "emails":self.emails, "addresses":self.addresses} }
            else:
                return {"status": False, "data": None }
        except Exception as e:
            print(f'ERROR at extract_contact_information_from_website_url => url {web_site_url} : {str(e)}')
            return {"status": False, "data": str(e) }
            
    def extract_contact_inf_from_current_page(self):
        start_time = time.time()  
        emails, phones = self.extract_contact_info_from_page()
        self.phones += phones
        self.emails += emails
        html_source = self.driver.page_source
        results = self.extract_contact_info_with_OpenAI_API(html_source)
        self.emails += list(results['content']['emails'])
        self.phones += list(results['content']['phones'])
        self.addresses += list(results['content']['addresses'])
        end_time = time.time() 
        execution_time = end_time - start_time 
        print(f"Temps d'exécution extract_contact_inf_from_current_page: {execution_time} secondes")
        
    def extract_contact_info_from_page(self):
        # Trouver toutes les balises <a> de la page
        liens = self.driver.find_elements(By.TAG_NAME, "a")
        
        # Listes pour stocker les e-mails et téléphones
        emails = []
        phones = []
        
        # Boucler sur chaque lien trouvé
        for lien in liens:
            href = lien.get_attribute("href")  # Extraire l'attribut href
            
            # Vérifier si le lien est un mailto:
            if href and "mailto:" in href:
                emails.append(href.split("mailto:")[1])  # Extraire l'adresse e-mail
            
            # Vérifier si le lien est un tel:
            elif href and "tel:" in href:
                phones.append(href.split("tel:")[1])  # Extraire le numéro de téléphone
        emails = list(set(emails))
        phones = list(set(phones))
        return emails, phones

    def extract_contact_info_with_OpenAI_API(self, html_source):
        clean_text = self.pageProcessing.get_clean_html_text_from_source_page(html_source)
        new_clean_text = self.sentenceProcessing.get_new_clean_text(clean_text)
        results = self.contactOpenAIScraping.predict(new_clean_text)
        return results
    ########################################################################################################
    ########################################################################################################
    def send_connection_invitation_from_profile_url(self, profile_url, message=None):
        if str(self.driver.current_url) != str(profile_url):
            self.driver.get(profile_url)
            time.sleep(random.uniform(3,4.5))
        
        div_buttons = self.get_element('/html/body/div[6]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]')
        if div_buttons['status'] :
            div_buttons = div_buttons['data']
        else :
            div_buttons = self.get_element('/html/body/div[5]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]')
            if div_buttons['status'] :
                div_buttons = div_buttons['data']
            else :
                div_buttons = self.get_element('//div[@class="ph5 pb5" or @class="ph5 " or contains(@class, "ph5") or contains(@class, "pb5")]')
                if div_buttons['status'] :
                    div_buttons = div_buttons['data']
                else :
                    print(div_buttons)

        if 'se connecter' in str(div_buttons.get_attribute('innerText')).lower():
            print('start with se connecter-----------------------------------------------------------------------------------------')
            button_se_connecter = self.get_element('//div/button', group= True, innerTextLower='se connecter', from_elem=div_buttons)
            if button_se_connecter['status'] :
                button_se_connecter = button_se_connecter['data']
                self.click_elem(button_se_connecter)
                time.sleep(random.uniform(1,2.5))
                if message:
                    self.add_message_to_connection_invitation(message=message)
                else:
                    button_envoyer_sans_note = self.get_element('//div/button', group=True, innerTextLower='envoyer sans note')
                    if button_envoyer_sans_note['status'] :
                        button_envoyer_sans_note = button_envoyer_sans_note['data']
                        self.click_elem(button_envoyer_sans_note)
            else:
                print(button_se_connecter)
            ############################################# plus ############################################
            button_plus = self.get_element('//div/button/span', group= True, innerTextLower='plus', from_elem=div_buttons)
            if button_plus['status'] :
                button_plus = button_plus['data']
                self.click_elem(button_plus)
                time.sleep(random.uniform(2,3.5))
                print('--> plus is clecked')
                
                button_suivre = self.get_element('//div/span', group= True, innerTextLower='suivre', from_elem=div_buttons)
                if button_suivre['status'] :
                    button_suivre = button_suivre['data']
                    self.click_elem(button_suivre)
                    print(f'2 ==> yes button_suivre dans plus ... {button_suivre.text}')
                else:
                    print(f'2 ==> suivre n\'existe pas dans plus...')
        

        if 'suivre' in str(div_buttons.get_attribute('innerText')).lower():
            print('start with suivre------------------------------------------------------------------------------------------------')
            button_suivre = self.get_element('//div/button/span', group=True, innerTextLower='suivre', from_elem=div_buttons)
            if button_suivre['status'] :
                button_suivre = button_suivre['data']
                self.click_elem(button_suivre)
                i = 5
                while i<5 and str(button_suivre.text).lower().strip() == 'suivre':
                    self.click_elem(button_suivre)
                    i += 1
                    time.sleep(random.uniform(0.5,1))
                print(f'1 ==> yes suivre in div_buttons')
                
            else:
                print(button_suivre)
            
            ############################################# plus ############################################
            button_plus = self.get_element('//div/button/span', group= True, innerTextLower='plus', from_elem=div_buttons)
            if button_plus['status'] :
                button_plus = button_plus['data']
                self.click_elem(button_plus)
                time.sleep(random.uniform(2,3.5))
                print('--> plus is clecked')
                    
                button_se_connecter = self.get_element('//div/span', group=True, innerTextLower='se connecter', from_elem=div_buttons)
                if button_se_connecter['status'] :
                    button_se_connecter = button_se_connecter['data']
                    
                    self.click_elem(button_se_connecter)
                    self.click_elem(button_plus)
                    time.sleep(1)
                    self.click_elem(button_se_connecter)
                    print(f'3 ==> yes se connecter in plus {button_se_connecter.get_attribute('innerText')}')
                    
                    if message:
                        self.add_message_to_connection_invitation(message=message)
                    else:
                        button_envoyer_sans_note = self.get_element('//div/button', group= True, innerTextLower='envoyer sans note')
                        if button_envoyer_sans_note['status'] :
                            button_envoyer_sans_note = button_envoyer_sans_note['data']
                            self.click_elem(button_envoyer_sans_note)
                
                else:
                    print(button_se_connecter)
            else:
                print(button_plus)
                
        return div_buttons

    def add_message_to_connection_invitation(self, message=''):
        button_ajouter_une_note = self.get_element('//div/button[@aria-label="Ajouter une note"]', group=True, innerTextLower='ajouter une note')
        if button_ajouter_une_note['status'] :
            button_ajouter_une_note = button_ajouter_une_note['data']
            self.click_elem(button_ajouter_une_note)
            time.sleep(1)
        else:
            print(button_ajouter_une_note)
            
        textarea_custom_message = self.get_element('//textarea[@id="custom-message"]')
        if textarea_custom_message['status'] :
            textarea_custom_message = textarea_custom_message['data']
            textarea_custom_message.send_keys(message)
        else:
            print(textarea_custom_message)
            
        time.sleep(1)
        button_envoyer = self.get_element('//div/button[@aria-label="Envoyer une invitation"]', group=True, innerTextLower='envoyer')
        if button_envoyer['status'] :
            button_envoyer = button_envoyer['data']
            self.click_elem(button_envoyer)
        else:
            print(button_envoyer)
    
    ########################################################################################################
    ########################################################################################################
    def extract_urls_from_linkedin_profiles_in_my_network(self):
        pass
    
    def extract_urls_from_linkedin_profiles_in_sales_navigator(self, filter_dic):
        pass
    
    def extract_posts_from_linkedin_profile_url(self, profile_url):
        pass
        
    def check_if_a_linkedin_profile_is_open_inmail_or_not(selfx, profile_url):
        pass
        
    def send_message_to_LinkedIn_profile_open_inmail(self, message, profile_url):
        pass
    