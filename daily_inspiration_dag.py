import json
import os
import requests
import pendulum
from airflow import DAG
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

class APIError(Exception):
    '''Custom exception for API request errors.'''
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code

def get_image():
    '''Retrieve the URL of an image from the Pexels API.'''
    access_key = os.getenv('PEXELS_API_KEY')
    headers = {'Authorization': access_key}
    url = 'https://api.pexels.com/v1/curated'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise APIError(f'Failed to retrieve image: {response.text}', response.status_code)
    image_url = response.json()['photos'][0]['src']['original']
    return image_url

def get_quote():
    '''Retrieve a daily inspirational quote from the Quotes API.'''
    api_key = os.getenv('QUOTES_API_KEY')
    url = f'https://quotes.rest/qod.json?category=inspire&api_key={api_key}'
    response = requests.get(url)
    if response.status_code != 200:
        raise APIError(f'Failed to retrieve quote: {response.text}', response.status_code)
    quote = response.json()['contents']['quotes'][0]['quote']
    return quote

def send_to_teams(image_url, quote):
    '''Send the retrieved image and quote to a Microsoft Teams channel.'''
    webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
    headers = {'Content-Type': 'application/json'}
    message = {
        '@type': 'MessageCard',
        '@context': 'http://schema.org/extensions',
        'summary': 'Daily Inspiration',
        'sections': [{
            'activityTitle': 'Send by Anna Gaplanyan:',
            'text': quote,
            'images': [{'image': image_url}]
        }]
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(message))
    return response.text

def main(ti):
    image_url = ti.xcom_pull(task_ids='get_image')
    quote = ti.xcom_pull(task_ids='get_quote')
    result = send_to_teams(image_url, quote)
    print(result)

with DAG(
    dag_id='daily_inspiration_dag',
    start_date=pendulum.today('UTC').add(days=-1),
    schedule_interval='@daily',
    tags=['inspiration'],
    description='A DAG to send daily inspirational quotes and images to Microsoft Teams',
    catchup=False,
) as dag:

    start_op = EmptyOperator(task_id='start')

    get_image_op = PythonOperator(
        task_id='get_image',
        python_callable=get_image
    )

    get_quote_op = PythonOperator(
        task_id='get_quote',
        python_callable=get_quote
    )

    send_to_teams_op = PythonOperator(
        task_id='send_to_teams',
        python_callable=main
    )

    finish_op = EmptyOperator(
        task_id='finish',
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )

    start_op >> [get_image_op, get_quote_op] >> send_to_teams_op >> finish_op
