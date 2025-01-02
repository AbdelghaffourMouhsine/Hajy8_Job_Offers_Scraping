class Item:
    # attributes = [ 'index', 'company_name', 'company_size', 'company_linkedin_url',
    #                'Secteur', 'Spécialisations', 'Profile_name', 'Profile_role',
    #                'Profile_linkedin', 'job_source', 'key_words', 'job_title',
    #                'job_description', 'job_url'

    #               # # Columns to added
    #               'phones', 'emails', 'addresses',
    #               # # profiles
    #               'profiles', 'profile_name', 'profile_description', 'profile_url',
                  
    #               'profile_address', 'country',
                  
    #               'linkedin_about_info', 'about téléphone', 'about taille de l’entreprise',
    #               'about page vérifiée', 'about site web','about spécialisations','about secteur','about siège social','about fondée en','about company_size',
    #               'about vue d’ensemble', 'min_size', 'max_size'
    #              ]
    
    attributes = ['company_name', 'company_linkedin_url', 'job_inf', 'job_url', 'job_title', 'job_mode','company_size', 'min_size', 'max_size', 'Secteur',
                  'job_skills', 'job_description', 'key_words'

                  # # Columns to added
                  # 'phones', 'emails', 'addresses',
                  # # profiles
                  'profiles', 'profile_name', 'profile_description', 'profile_url',
                  
                  # 'profile_address', 'country',
                  
                  # 'linkedin_about_info', 'about téléphone', 'about taille de l’entreprise',
                  # 'about page vérifiée', 'about site web','about spécialisations','about secteur','about siège social','about fondée en','about company_size',
                  # 'about vue d’ensemble'
                 ]
    
    def __init__(self, dict=None):
        for attribute in self.attributes:
            setattr(self, attribute, None)
        if dict:
            for attr_name, attr_value in self.__dict__.items():
                setattr(self, attr_name, dict.get(attr_name))
            
    def init_from_dict(self, dict):
        for attr_name, attr_value in self.__dict__.items():
            setattr(self, attr_name, dict.get(attr_name))

    def to_dict(self):
        return self.__dict__
        
    def __str__(self):
        return str(self.to_dict())

class Company:
    
    attributes = ['company_name', 'company_linkedin', 'company_website', 'company_size', 'min_size', 'max_size', 'secteur', 'phones', 'emails', 'addresses',
                  'profiles', 'country', 'linkedin_about_info', 'about_téléphone', 'about_taille_de_l_entreprise', 'about_page_vérifiée',
                  'about_site_web','about_spécialisations','about_secteur','about_siège_social','about_fondée_en','about_company_size', 'about_vue_d_ensemble'
                 ]
    
    def __init__(self, dict=None):
        for attribute in self.attributes:
            setattr(self, attribute, None)
        if dict:
            for attr_name, attr_value in self.__dict__.items():
                setattr(self, attr_name, dict.get(attr_name))
            
    def init_from_dict(self, dict):
        for attr_name, attr_value in self.__dict__.items():
            setattr(self, attr_name, dict.get(attr_name))

    def to_dict(self):
        return self.__dict__
        
    def __str__(self):
        return str(self.to_dict())

class Job:
    
    attributes = ['company_name', 'company_linkedin', 'company_website', 'job_url', 'job_title', 'job_inf', 'job_mode','company_size', 'min_size', 'max_size',
                  'secteur', 'job_skills', 'job_description', 'job_location', 'job_date', 'job_source', 'key_words',

                  # Columns to added
                  
                  # 'phones', 'emails', 'addresses',
                  # 'profiles', 'profile_name', 'profile_description', 'profile_url',
                  # 'profile_address', 'country',
                  # 'linkedin_about_info', 'about téléphone', 'about taille de l’entreprise',
                  # 'about page vérifiée', 'about site web','about spécialisations','about secteur','about siège social','about fondée en','about company_size',
                  # 'about vue d’ensemble'
                 ]
    
    def __init__(self, dict=None):
        for attribute in self.attributes:
            setattr(self, attribute, None)
        if dict:
            for attr_name, attr_value in self.__dict__.items():
                setattr(self, attr_name, dict.get(attr_name))
            
    def init_from_dict(self, dict):
        for attr_name, attr_value in self.__dict__.items():
            setattr(self, attr_name, dict.get(attr_name))

    def to_dict(self):
        return self.__dict__
        
    def __str__(self):
        return str(self.to_dict())