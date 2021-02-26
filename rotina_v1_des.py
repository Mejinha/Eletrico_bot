# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 19:22:18 2021

@author: amejd
"""

import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import tweepy


def web_scrapping(start_date = 'today', offset = 8):
    '''
    Scrap data from the ONS page and return a pandas dataframe   
    
    Parameters
    ----------
    start_date : str, optional
        The last day of analysis. The default is 'today'.
    offset : int, optional
        Moving average window + 1. The default is 8.

    Returns
    -------
    Pandas dataframe

    '''
    
    # Obter datas de início e fim
    
    last_day = np.datetime64(start_date) - 1
    first_day = last_day - offset
    
    # Obter intervalo de datas
    
    day_range = np.arange(first_day, last_day)
    
    dataraw = {'hidro': {},
               'itaipu': {},
               'nuclear': {},
               'termo': {},
               'eolica': {},
               'solar': {}}
    
    for day in day_range:
        
        #Converter data no formato adequado
        date = pd.to_datetime(str(day)).strftime('%Y_%m_%d')
        
        #Enviar request
        response = requests.get(fr'http://sdro.ons.org.br/SDRO/DIARIO/{date}/HTML/01_RelBalancoEnergeticoDiario.html')
        
        #Buscar dados
        soup = BeautifulSoup(response.content, 'html.parser')       
        
        #Criar dicionário por fontes
        dataraw['hidro'][str(day)] = float(soup.select('#lbl_sin_hidro_v')[0].text) * 24
        dataraw['itaipu'][str(day)] = float(soup.select('#lbl_sin_itaipu_v')[0].text) * 24
        dataraw['nuclear'][str(day)] = float(soup.select('#lbl_sin_nuclear_v')[0].text) * 24
        dataraw['termo'][str(day)] = float(soup.select('#lbl_sin_termo_v')[0].text) * 24
        dataraw['eolica'][str(day)] = float(soup.select('#lbl_sin_eolica_v')[0].text) * 24
        dataraw['solar'][str(day)] = float(soup.select('#lbl_sin_eolica_v')[0].text) * 24
        
    return dataraw

def emission_factor(dataframe, factor_dict):
    '''
    Calculate emission factors by multiplying each source by a dict value

    Parameters
    ----------
    dataframe : Pandas DataFrame
        Emissions data.
    factor_dict : dict
        Emission factors.

    Returns
    -------
    factor : Pandas DataFrame
        Emissions of each technology.

    '''
    
    factor = dataframe.copy()
    
    for source in dataframe.columns:
        factor[source] = dataframe[source] * factor_dict[source]

    return factor

def calculate_average(dataframe):
    '''
    Calculate average of the past days

    Parameters
    ----------
    dataframe : Pandas DataFrame
        Dataframe by source.

    Returns
    -------
    mean : dict
        Dictionary of means by source.

    '''
    
    mean = {}
    
    for source in dataframe.columns:
        mean[source] = dataframe[source][:-1].mean()
        
    return mean

def calculate_variation(dataframe, ma):
    '''
    Calculate variation compared to the moving average

    Parameters
    ----------
    dataframe : Pandas DataFrame
        Dataframe by source.
    ma : dict
        Dictionary of moving average.

    Returns
    -------
    rate : float
        Rate of change of the data.

    '''
    
    total_past = np.sum(list(ma.values()))
    total_present = dataframe[-1:].sum(axis = 1)[0]

    rate = total_present / total_past - 1
    
    return rate
    
def write_tweet(rate, emissions, dataframe):
    '''
    Write a tweet

    Parameters
    ----------
    rate : float
        Rate of change.
    emissions : Pandas DataFrame
        Emissions.
    dataframe : Pandas DataFrame
        Generation.

    Returns
    -------
    tweet : str
        Tweet.

    '''
    
    percentual_semana = np.round(rate * 100,1)
    
    if percentual_semana > 0:
        comparador = 'mais'
        emoji_seta = '🌡'
        emoji_comparador = '☹'
    else:
        comparador = 'menos'
        emoji_seta = '☘'
        emoji_comparador = '😀'
        
    co2 = np.round(emissions[-1:].sum(axis = 1)[0], 0)
    gwh = np.round(dataframe[-1:].sum(axis = 1)[0], 0)

    tweet = f"Emitimos {co2} toneladas de CO2 para gerar {gwh} GWh e acender o Brasil ontem!" + \
    f"\nIsso equivale a {percentual_semana}% {comparador} emissões que a média da última semana {emoji_seta}{emoji_comparador}"

    return tweet

def publish_tweet(tweet):
    '''
    

    Parameters
    ----------
    tweet : str
        Tweet.

    Returns
    -------
    None.

    '''

    auth = tweepy.OAuthHandler("API KEY", "API SECRET")
    auth.set_access_token("ACCESS KEY", "ACCESS SECRET")
    
    
    # Create API object
    api = tweepy.API(auth)
    
    # Create a tweet
    api.update_status(tweet)
    
def Run():
    fator = {'hidro': 0,
          'itaipu': 0,
          'solar': 0,
          'eolica': 0,
          'nuclear': 0,
          'termo': 0.231413}
    
    data = pd.DataFrame(web_scrapping('today', 8))
    emissions = emission_factor(data, fator)
    medias = calculate_average(emissions)
    rate = calculate_variation(emissions, medias)
    tweet = write_tweet(rate, emissions, data)
    print(tweet)
    publish_tweet(tweet)    
    
if __name__ == '__main__':
    
    Run()
