from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import os
from dotenv import load_dotenv

class ContactOpenAIScraping:

    def __init__(self):
        # Charger les variables d'environnement depuis le fichier .env
        load_dotenv('settings.env')
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo-1106",
            temperature=.3,
            max_tokens=None,
            timeout=None,
            max_retries=3,
            api_key = self.api_key,
        )
        messages = [
            (
                "system", """You are an agent tasked with extracting contact information (emails, phone numbers, fax numbers, WhatsApp numbers, and addresses) from a contact page text.
            
                => Only extract valid information that is actually present in the provided text. Do not generate or include any placeholder data such as 'info@company.com', 'support@company.com', '123-456-7890', '+1234567890', or any similar non-existent contacts.
                => Make sure the value of the key "phones" contains all valid phone numbers, fax numbers, and WhatsApp numbers.
                => Ensure the value of the key "addresses" contains valid, identifiable addresses.
                => Ensure you identify and extract the relevant information accurately.
                """
            ),
            (
                "human", """Extract the contact information (emails, phone numbers, and addresses) and format it into a JSON object from the following text. Make sure not to create any additional keys—only 'emails' and 'phones' and 'addresses'. Ensure the value of the key 'phones' contains all phone, fax, and WhatsApp numbers from the contact page text. If no information is found for any of the keys, the value should be an empty list (e.g., "emails": [], "phones": [], "addresses": [])."""
            ),
            (
                "human","{contact_page_text}"
            )
            ]
        
        self.json_llm = self.llm.bind(response_format={"type": "json_object"})
        self.template = ChatPromptTemplate.from_messages(messages)
        self.chain = self.template | self.json_llm
        
    def predict(self, input_contact_page_text):
        ai_msg = self.chain.invoke({'contact_page_text':input_contact_page_text})
        results = {}
        results['content'] = json.loads(ai_msg.content)
        results['completion_tokens'] = ai_msg.response_metadata['token_usage']['completion_tokens']
        results['prompt_tokens'] = ai_msg.response_metadata['token_usage']['prompt_tokens']
        results['total_tokens'] = ai_msg.response_metadata['token_usage']['total_tokens']
        results['model_name'] = ai_msg.response_metadata['model_name']
        return results




class FoundersOpenAIClassification:

    def __init__(self):
        load_dotenv('settings.env')
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo-1106",
            temperature=.3,
            max_tokens=None,
            timeout=None,
            max_retries=3,
            api_key = self.api_key,
        )
        messages = [
            (
                "system", """
                Your task is to classify a list of LinkedIn profile descriptions into two categories: "founder" and "non-founder." Profiles considered as "founder" should have a job title matching one of the following: "general director" (either "directeur général" or "directrice générale"), "CEO," "president" (either "président" or "présidente"), "founder" (either "fondateur" or "fondatrice"), "co-founder, "CTO", "HR director" (either "DRH (directeur RH)" or "DRH (directrice RH)"), "partner" (either "associé" or "associée"), "CFO", "Chief" (not "chef"), or "CEO" (either "PDG"). If the profile matches any of these titles, it should be classified as "founder" with a value of True. All other profiles should be classified as "non-founder" with a value of False.

The output format should be in JSON, where each key represents the profile's name and the value is True if the profile is a "founder", and False otherwise.
                """
            ),
            (
                "human", """
                [
                    "Jean Dupont, CEO and co-founder of an innovative startup",
                    "Marie Martin, software developer at a tech company",
                    "Alexandre Leblanc, general director of a consulting firm",
                    "Sophie Bernard, marketing manager",
                    "Isabelle Dubois, founder of a design company",
                    "Claire Durand, HR director at a large corporation"
                ]
                """
            ),
            (
                "ai", """
                {{
                    "Jean Dupont": true,
                    "Marie Martin": false,
                    "Alexandre Leblanc": true,
                    "Sophie Bernard": false,
                    "Isabelle Dubois": true,
                    "Claire Durand": true
                }}
                """
            ),
            (
                "system","""Make sure the output is well-structured and follows the given criteria, treating titles like "director" and "directress" (and their equivalents for other positions) as equivalent.
                """
            ),
            (
                "human","{list_profiles}"
            )
            ]
        
        self.json_llm = self.llm.bind(response_format={"type": "json_object"})
        self.template = ChatPromptTemplate.from_messages(messages)
        self.chain = self.template | self.json_llm
        
    def predict(self, list_profiles):
        ai_msg = self.chain.invoke({'list_profiles':list_profiles})
        results = {}
        results['content'] = json.loads(ai_msg.content)
        results['completion_tokens'] = ai_msg.response_metadata['token_usage']['completion_tokens']
        results['prompt_tokens'] = ai_msg.response_metadata['token_usage']['prompt_tokens']
        results['total_tokens'] = ai_msg.response_metadata['token_usage']['total_tokens']
        results['model_name'] = ai_msg.response_metadata['model_name']
        return results


class FilterFoundersOneByOneOpenAI:

    def __init__(self):
        load_dotenv('settings.env')
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo-1106",
            temperature=.3,
            max_tokens=None,
            timeout=None,
            max_retries=3,
            api_key = self.api_key,
        )
        messages = [
            (
                "system", """
                Your task is to classify a single LinkedIn profile description as either "founder" (True) or "non-founder" (False). A profile should be classified as "founder" (True) if the job title matches one of the following:
                
"general director" ("directeur général" or "directrice générale")
"CEO" ("PDG")
"president" ("président" or "présidente")
"founder" ("fondateur" or "fondatrice")
"co-founder"
"CTO"
"CFO"
"Chief"
"HR director" ("DRH" - "directeur RH" or "directrice RH")
"partner" ("associé" or "associée")
"owner" (but not "product owner")
"Investor" ("investeur")
"Entrepreneur"
If the profile's job title contains any of these roles, it should be classified as "founder" with a json response of {{"response": true}}. All other profiles should be classified as "non-founder" with a json response of {{"response": false}}. Treat titles like "director" and "directress" as equivalent."""
            ),
            (
                "human", "CEO of a tech company"
            ),
            (
                "ai", """{{"response": true}}"""
            ),
            (
                "human", "charge des ressources humaines"
            ),
            (
                "ai", """{{"response": false}}"""
            ),
            (
                "system","""Make sure the output is well-structured and follows the given criteria, treating titles like "director" and "directress" (and their equivalents for other positions) as equivalent.
                """
            ),
            (
                "human","{profile}"
            )
            ]
        
        self.json_llm = self.llm.bind(response_format={"type": "json_object"})
        self.template = ChatPromptTemplate.from_messages(messages)
        self.chain = self.template | self.json_llm
        
    def predict(self, profile):
        ai_msg = self.chain.invoke({'profile':profile})
        results = {}
        results['content'] = json.loads(ai_msg.content)
        results['completion_tokens'] = ai_msg.response_metadata['token_usage']['completion_tokens']
        results['prompt_tokens'] = ai_msg.response_metadata['token_usage']['prompt_tokens']
        results['total_tokens'] = ai_msg.response_metadata['token_usage']['total_tokens']
        results['model_name'] = ai_msg.response_metadata['model_name']
        return results