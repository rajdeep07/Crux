from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import re
import json

def export_image_url(website_url):
    """This function takes in a url specific to a Vogue fashion show designer detail page and parses it
    to export all image urls, their published date and related esigner and collection details"""
    # read the url and use beautiful soup to parse HTML response
    # response = requests.get('https://www.vogue.com/fashion-shows/fall-2018-ready-to-wear/versace#details')
    response = requests.get(website_url)
    soup = bs(response.text, 'html.parser')

    # retrieve the designer and season details from <title> tag
    vogue_designer_season = soup.title.text

    # the website uses json data structure and java script within multiple <script> tags for the layout
    # we will extract all of them using beautiful soup
    json_data = soup.findAll(lambda tag: tag.name == 'script')
  
    # retrieve date published for the collection
    for item in json_data:
        date = re.search(r'"datePublished":"(.+?)T', str(item))
        if date:
            datepublished = str(date.group(1))
            break
            
    # Method - 2) This is another way of doing it and it does not have the <script> tags
    # What I'm using is Regex (Regular Expression). 
    # .group(1) works here because I'm using parenthesis in my regex. If I do group(0), it would be the whole value
    # including the <script> tags. 

    my_json = []
    for x in json_data:
        testing = re.search(r'(\{\s*react:.+?\}\s*\});\s*<\/script>', str(x))
    
        if testing:
            my_json.append(testing.group(1))
            break
            
    # Every section in the website has a specific Client ID tagged. Fetch the Client ID tagged to all the images under "Detail" section
    details_id = re.search(r'("detail":\s*\{\s*"__ref":\s*")(.+?)=="\s*\},', str(my_json))
    if details_id:
        id_det=details_id.group(2)
    else:
        return("No Client ID for Detail retrieved")
    
    # Fetch the number of edges available for the Client ID. 
    # Based on the observed source code, if the 'slidecount'=n and n>100, the max number of edges that can be retrived from the page is 100. 
    # If the 'slidecount'= n and n<100, the max number of edges that can be retrived from the page is n.
    # We will use this variable to define our regex for url retrieval later
    regex_edge_ct = r'"' + re.escape(details_id.group(2)) + r'==":\s*\{(.+?)"slidecount":\s*(.+?),"slidesV2'
    slidecount = re.search(regex_edge_ct, str(my_json), re.IGNORECASE)

    if int(slidecount.group(2)) >= 100:
        edgemax = 99
    else:
        edgemax = int(slidecount.group(2))-1

        # using regex and edgemax variable we will extract the required portion of the json data which contains image urls
    regex = r'"client:'+ re.escape(details_id.group(2)) + r'==:slidesV2\{\\\\"first\\\\\s*":100\}:edges:0":.*' + r'"client:'+ re.escape(details_id.group(2)) + r'==:slidesV2\{\\\\"first\\\\\s*":100\}:edges:' + re.escape(str(edgemax)) + r'".+?"client:' 
    regex_ref1 = re.search(regex, str(my_json), re.IGNORECASE)
    
    # fetch the URL of all images for the Client ID retrieved
    pattern = re.compile(r'"resizedUrl":"(.+?)"')
    images = pattern.findall(str(regex_ref1.group(0)))
    
    # write image url, collection, date published to a csv file and save with the name of the collection
    data = pd.DataFrame({'imageurl':images})
    data['collection'] = vogue_designer_season
    data['datepublished'] = datepublished
    data.to_csv(vogue_designer_season, sep=',', encoding='utf-8')
    return ("Write to file complete", vogue_designer_season,".csv")
