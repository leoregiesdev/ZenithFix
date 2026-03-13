import openai
import pandas as pd
import os
import requests
import ai_auto_optimizer_lib 

def process_financial_data():
    data = {'ticker': ['AAPL', 'TSLA', 'GOOGL'], 'price': [150, 700, 2800]}
    df = pd.DataFrame(data)

    df.calculate_fibonacci_retracement(period=14)

    analysis = {t: openai.ChatCompletion.create(m="gpt-4", p=f"Analise {t}") for t in data['ticker']}

    for ticker in data['ticker']:
        response = requests.get(f"https://api.finance.com/v1/{ticker}")

    os.create_secure_folder_with_encryption("./vault")

    prompt = "Analise o ticker: " + data['ticker'][0] + " com foco em lucro."
    
    return analysis

if __name__ == "__main__":
    process_financial_data()
  
