import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import yaml

load_dotenv()

with open("prompts.yaml", "r") as f:
    prompts = yaml.safe_load(f)

class GenerateEmail():    
    def __init__(self, model: str):
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.deployment_name = model

    def _call_api(self, messages):
        # TODO: implement this function to call ChatCompletions
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.8,
                max_tokens=400
            )
            return response.choices[0].message.content
        except Exception as e:
            if "RateLimitReached" in str(e):
                return "Rate Limit Exceeded: You have exceeded the free tier rate limit. Please try again later or upgrade your plan."
            else:
                return f"Error: {str(e)}"
    
    def get_prompt(self, prompt_name, prompt_type='user', **kwargs):
        template = prompts[prompt_name][prompt_type]
        return template.format(**kwargs)
    
    def evalResponse(self, reference_email, result_email, metric_name, judge_model):
        ref_content = reference_email['content'].replace('{', '{{').replace('}', '}}')
        res_content = result_email['content'].replace('{', '{{').replace('}', '}}')
        metric_data = prompts['evaluation'][metric_name]
        motive = metric_data['motive']
        criteria = metric_data['criteria']
        rating_levels = metric_data['rating_levels']
        prompt_template = prompts['evaluation_template']
        try:
            response = self.client.chat.completions.create(
                model=judge_model,
                messages=[
                    {"role": "user", "content": prompt_template.format(email_content=ref_content, result_email_content=res_content, criteria=criteria, motive=motive, rating_levels=rating_levels)}
                ],
                temperature=0.7,
                max_tokens=200
            )
            extracted_text = response.choices[0].message.content
            try:
                evaluation = json.loads(extracted_text)
                rating = evaluation.get("Rating", "N/A")
                reason = evaluation.get("Reason", "N/A")
            except json.JSONDecodeError:
                reason = extracted_text.strip()
                rating = "N/A"
            return rating, reason
        except Exception as e:
            if "RateLimitReached" in str(e):
                return "Rate Limit Exceeded", "You have exceeded the free tier rate limit. Please try again later or upgrade your plan."
            else:
                return "Error", f"An error occurred: {str(e)}"
    
    def send_prompt(self, user_prompt: str, system_msg="You are a helpful assistant."):
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ]
        return self._call_api(messages)
    
    def generate(self, action: str, content: str, **kwargs):
        # TODO: implement your backend logic with this method. Skeleton code is provided below.
        if action == "shorten":
            args = {
                "content": content
            }
            system_prompt = self.get_prompt('shorten', prompt_type='system', **args)
            user_prompt = self.get_prompt('shorten', **args)
            print("system prompt:", system_prompt)
            print("user prompt:", user_prompt)
            model_response = self.send_prompt(user_prompt, system_prompt)
            return model_response
        elif action == "elaborate":
            args = {
                "content": content
            }
            system_prompt = self.get_prompt('elaborate', prompt_type='system')
            user_prompt = self.get_prompt('elaborate', **args)
            model_response = self.send_prompt(user_prompt, system_prompt)
            return model_response
        elif action == "tone":
            args = {
                "content": content,
                "tone": kwargs.get("tone", "professional")
            }
            system_prompt = self.get_prompt('tone', prompt_type='system', **args)
            user_prompt = self.get_prompt('tone', **args)
            model_response = self.send_prompt(user_prompt, system_prompt)
            return model_response