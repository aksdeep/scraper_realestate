import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import ast
import re
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

def get_text_from_html(city):
    ''' This returns text from HTML Website'''
    page = requests.get("https://www.domain.com.au/auction-results/"+city)
    print(page)
    soup = BeautifulSoup(page.content, 'html.parser')
    html = list(soup.children)[3]
    body = list(html.children)[3]
    div = list(body.children)[2]
    

    return div

def div_to_dict_json(div, filename):
    paragraphs = []
    for x in div:
        paragraphs.append(str(x))
    string_div = paragraphs[0]
    string_div = string_div[:-59]
    string_div = string_div[37:]


    i = 0 
    dictionary_info = []
    for x in string_div:
        i = i+1
        dictionary_info.append(x)

    dictionary_info = ''.join(dictionary_info)

    with open(filename,'w') as file:
        file.write(dictionary_info)

def get_df_from_json_file(filename):
    with open(filename) as file:
        data = file.read()
    data = json.loads(data)
    sales_listings_all = data["salesListings"]
    print(sales_listings_all)
    passed_in_list = []
    for suburb in sales_listings_all:
        suburb_name = suburb['suburb']
        each_suburb = suburb['listings']
        for listing in each_suburb:
            if listing["result"]=='AUVB' or listing["result"]=='AUHB' or listing["result"]=='AUPI' :
                if 'price' in listing:
                    if listing["price"]<=850000 and listing['propertyType']!='Unit' and listing['propertyType']!='Townhouse':
                        try:
                            passed_in_auctions = (listing["streetNumber"],  listing["streetName"],listing["streetType"], suburb_name)
                        except:
                            passed_in_auctions = (listing["streetNumber"],  listing["streetName"], suburb_name)
                        passed_in_property = ' '.join(passed_in_auctions)
                        passed_in_property = multiple_replace(passed_in_property)
                        passed_in_dict = {'passed_in_property': passed_in_property, 'price_in_auction': listing["price"]}
                        passed_in_list.append(passed_in_dict)
                else:
                    try:
                        passed_in_auctions = (listing["streetNumber"],  listing["streetName"],listing["streetType"], suburb_name)
                    except:
                        passed_in_auctions = (listing["streetNumber"],  listing["streetName"], suburb_name)
                    passed_in_property = ' '.join(passed_in_auctions)
                    passed_in_property = multiple_replace(passed_in_property)
                    passed_in_dict = {'passed_in_property': passed_in_property, 'price_in_auction': 0}
                    passed_in_list.append(passed_in_dict)
    df = pd.DataFrame(passed_in_list)
    return df

def multiple_replace(text):
    dict = {"St " : "Street ","Wy " : "Way ","Av " : "Avenue ","Rd " : "Road ","Dr " : "Drive ","Ct " : "Court ","Cr "  : "Crescent ",}
    
    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))
    
    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

def search_on_the_house(df_auction_results):
    passed_in_cleaned_list = df_auction_results.passed_in_property.values
    passed_in_cleaned_list = passed_in_cleaned_list.tolist()
    i=0 ## For counting the number
    N=50 ## For number of backspaces
    printed_results = []
    for passed_in_property in passed_in_cleaned_list:
        i = i+1
        if i<len(passed_in_cleaned_list)-10:
            if i == 1:
                driver = webdriver.Chrome('/Users/akash/Desktop/chromedriver')
                driver.get('https://www.onthehouse.com.au/real-estate/')
                time.sleep(3)
            #builder.send_keys(Keys.COMMAND, Keys.LEFT_ALT, 'j')
            search_bar = driver.find_element_by_css_selector("input[placeholder='Enter an address, suburb or postcode']")
            time.sleep(3)
            search_bar.send_keys(Keys.BACKSPACE * N)
            time.sleep(4)
            search_bar.send_keys(passed_in_property)
            time.sleep(4)
            search_bar.send_keys(Keys.RETURN)
            time.sleep(5)
            try:
                element = driver.find_element(By.XPATH, '//*[@id="topOfSearchResults"]/div/div[1]/div/div[1]/div[3]/div/span')
                passed_in_dict = {'passed_in_property': passed_in_property, 'price_from_on_the_house': element.text}
            # except('NoSuchElementException'):
            #     element = driver.find_element(By.XPATH,'//*[@id="topOfSearchResults"]/div/div[1]/div/div[1]/div[4]/div/div[1]')
            #     passed_in_dict = {'passed_in_property': passed_in_property, 'price_from_on_the_house': element.text}
            except:
                passed_in_dict = {'passed_in_property': passed_in_property, 'price_from_on_the_house': 0}
                
            printed_results.append(passed_in_dict)
            time.sleep(4) # sleep for 5 seconds so you can see the results
    df_on_the_house = pd.DataFrame(printed_results)
    return df_on_the_house
            

def main():
    city = 'melbourne'
    div = get_text_from_html(city)
    div_to_dict_json(div, city+'.json')
    df_auction_results = get_df_from_json_file(city+'.json')
    df_on_the_house = search_on_the_house(df_auction_results)
    
    ## Similar to SQL
    complete_df = pd.merge(df_auction_results, df_on_the_house)
    complete_df.to_csv("/Users/akash/Desktop/auctionresults.csv")

if __name__ == "__main__":
    main()
