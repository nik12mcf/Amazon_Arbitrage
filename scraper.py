import requests
from bs4 import BeautifulSoup
import keepa
from requests_html import HTMLSession
import csv
import os
import pandas as pd
import math

accesskey = '10vutnklo14hd1185d1j22ffukjll3sar7rtovjcg00pvh9pvdkji0bc0795nc1u'
api = keepa.Keepa(accesskey)

websites = ["Kohls", "Carters", "Walmart", "Bed_Bath_And_Beyond", "Nike"]

rawAsinUpcDict = {}
finalAsinUpcDict = {}

kohlsFinalList = []
cartersFinalList = []

def checkKohls(asin, upc):
    # Parse Kohl's website
    startURL = 'https://www.kohls.com/search.jsp?submit-search=web-regular&search='
    endURL = '&kls_sbp=62335709326100253324335907950981413624'

    URL = startURL + upc + endURL
    try:
        page = requests.get(URL)
    except:
        return
    soup = BeautifulSoup(page.content, 'html.parser')

    # Did not find UPC at Kohl's website
    if soup.find(class_="search-term search-failed"):
        return
    # UPC was found successfully at Kohl's website
    else:
        print("Success at Kohls")
        if asin not in finalAsinUpcDict:
            finalAsinUpcDict[asin] = [upc]
        else:
            finalAsinUpcDict[asin].append(upc)

        try:
            amznLatestPrice = api.query(asin)[0]['data']['NEW'][-1]
        except:
            return

        # Find price at Kohls, also remove first char since it is '$'
        try:
            kohlsLatestPrice = soup.find(class_="pdpprice-row2-main-text").text.strip()[1:]
        except:
            return

        # Ensure valid price at Amzn and Kohls
        if(math.isnan(amznLatestPrice)):
            return

        try:
            float(kohlsLatestPrice)
        except:
            return

        kohlsFinalList.append([asin, upc, "Kohls", amznLatestPrice, kohlsLatestPrice])

        print(kohlsFinalList)

        return

def checkCarters(asin, upc):
    # Parse Carter's website
    startURL = 'https://www.carters.com/on/demandware.store/Sites-Carters-Site/default/Search-Show?q='
    endURL = '&simplesearchDesktop='

    URL = startURL + upc + endURL
    session = HTMLSession()
    try:
        response = session.get(URL)
    except:
        return

    # Did not find UPC at Carter's website
    if response.html.find('.search-result-title', first=True) != None:
        return
    # UPC was found successfully at Carter's website
    else:
        print("Success at Carters")
        if asin not in finalAsinUpcDict:
            finalAsinUpcDict[asin] = [upc]
        else:
            finalAsinUpcDict[asin].append(upc)

        try:
            amznLatestPrice = api.query(asin)[0]['data']['NEW'][-1]
        except:
            return

        # Must ensure price at Carters is correct
        try:
            cartersLatestPrice = response.html.find('.value', first=True).text
        except:
            return

        if cartersLatestPrice != "Out of Stock":
            cartersFinalList.append([asin, upc, "Carters", amznLatestPrice, cartersLatestPrice[1:]])

        print(cartersFinalList)

        return

def findCategories():
    categories = api.search_for_categories('baby')
    catids = list(categories.keys())
    for catid in catids:
        print(catid, categories[catid]['contextFreeName'])

def createAsinsCsv(catids):
    asins = []

    for catid in catids:
        bestsellers = api.best_sellers_query(catid)

        in_first = set(asins)
        in_second = set(bestsellers)

        in_second_but_not_in_first = in_second - in_first

        asins.extend(list(in_second_but_not_in_first))

        print("Scraped ASINS in category: ", catid)

    print("FINISHED SCRAPING AMAZON PRODUCTS")
    print("CREATING ASINS CSV FILE")

    fields = ['ASIN', 'Identifier', 'Purchasing Price']

    rows = []
    for asin in asins:
        rows.append([asin, 'asin', 5.00])

    for i in range(0, len(asins), 3000):
        filename = r"raw_asins\asins_" + str(int(i / 3000)) + ".csv"

        with open(filename, 'w', newline='') as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(csvfile)

            # writing the fields
            csvwriter.writerow(fields)

            # writing the data rows
            csvwriter.writerows(rows[i:i+3000])

def createAsinUpcDict():
    for filename in os.listdir(r'algopix_data'):
        print(filename)
        filepath = "algopix_data\\" + filename
        df = pd.read_excel(filepath)
        df = df[df['UPC'].notna()]

        keys = list(df['ASIN'])
        values = list(df['UPC'])

        for row in range(len(keys)):
            rawAsinUpcDict[keys[row]] = [str(int(values[row]))]

def crossCheckProducts():
    for asin in rawAsinUpcDict:
        upcList = rawAsinUpcDict[asin]

        for upc in upcList:
            print("Checking UPC: ", upc)

            checkKohls(asin, upc)
            #checkCarters(asin, upc)

def performStatistics():
    columns = ['asin', 'upc', 'store', 'amznPrice', 'storePrice', 'percentProfit']

    ################################## Kohls ##################################
    for list in kohlsFinalList:
        # Calculate percentage profit
        percentProfit = (float(list[3]) - float(list[4])) / float(list[4]) * 100
        percentProfit = "%.2f" % percentProfit
        list.append(float(percentProfit))

    dfKohlsFinal = pd.DataFrame(kohlsFinalList, columns=columns)
    dfKohlsFinal = dfKohlsFinal.sort_values(by=['percentProfit'], ascending=False)

    ################################# Carters #################################
    for list in cartersFinalList:
        # Calculate percentage profit
        percentProfit = (float(list[3]) - float(list[4])) / float(list[4]) * 100
        percentProfit = "%.2f" % percentProfit
        list.append(float(percentProfit))

    dfCartersFinal = pd.DataFrame(cartersFinalList, columns=columns)
    dfCartersFinal = dfCartersFinal.sort_values(by=['percentProfit'], ascending=False)

    print("Kohl's List")
    print(dfKohlsFinal)
    print("Carter's List")
    print(dfCartersFinal)

# Find categories on Amazon
#findCategories()

# Create a raw asin csv file to input into algopix to find the respective upc
#createAsinsCsv(['7628013011', '9057169011', '9057142011'])

# Read the algopix data and extract upc for respective asin then construct dict
createAsinUpcDict()

# Check to see if products found on Amazon can be found at department stores
crossCheckProducts()

#kohlsFinalList = [['B08K19Q9QM', '194573637616', 'Kohls', 16.48, '23.06'], ['B08K9CLJJK', '194133536472', 'Kohls', 24.99, '16.20'], ['B08G8VN5BS', '194133609664', 'Kohls', 13.99, '14.40'], ['B07FWL41RN', '191448503052', 'Kohls', 35.74, '39.99'], ['B07SBB4PJC', '191448445673', 'Kohls', 85.95, '29.99'], ['B082W63711', '194814415348', 'Kohls', 40.0, '34.99'], ['B0781ZTCR8', '682510815864', 'Kohls', 22.49, '30.00'], ['B07NH46GPF', '617847589959', 'Kohls', 48.01, '30.00'], ['B07JNK38VL', '192170513630', 'Kohls', 27.9, '24.74'], ['B07WFJ5MLS', '193150089381', 'Kohls', 49.9, '40.00'], ['B00XA7SAI4', '792850015302', 'Kohls', 38.03, '14.99'], ['B00OTE7QFA', '792850336995', 'Kohls', 7.46, '8.99'], ['B07FNZG13J', '764302224051', 'Kohls', 9.99, '9.99'], ['B07XTVKCHR', '851877006455', 'Kohls', 9.99, '9.99'], ['B0769LK11D', '817810027116', 'Kohls', 9.99, '11.99'], ['B000NC2MII', '792850336995', 'Kohls', 7.78, '8.99'], ['B07SRFY91V', '764302901402', 'Kohls', 26.89, '9.99'], ['B077BHSHKP', '792850019409', 'Kohls', 15.08, '9.99']]

# Organize and filter it final products for each department store
performStatistics()

# Kohls
# {'194573637616': ['B08K19Q9QM', '194573637616', 'Kohls', 16.48, '13.18'], '699302006560': ['B005W9MXWW', '699302006560', 'Kohls', 29.74, '34.99 - $54.99'], '194133536472': ['B08K9CLJJK', '194133536472', 'Kohls', 24.99, '14.40'], '194133609664': ['B08G8VN5BS', '194133609664', 'Kohls', 15.7, '12.80'], '191448503052': ['B07FWL41RN', '191448503052', 'Kohls', 35.76, '39.99'], '194133028090': ['B0863CKVMB', '194133028090', 'Kohls', 19.9, '7.04'], '191448445673': ['B07SBB4PJC', '191448445673', 'Kohls', 85.95, '29.99'], '194814415348': ['B082W63711', '194814415348', 'Kohls', 'nan', '24.99'], '193152381414': ['B07NLVR7L5', '193152381414', 'Kohls', 49.99, '33.75'], '191533780481': ['B0812L2G2R', '191533780481', 'Kohls', 'nan', '24.99'], '606725220817': ['B00B58A150', '606725220817', 'Kohls', 22.46, '26.39'], '191984329796': ['B0812L3RLL', '191984329796', 'Kohls', 'nan', '37.50'], '193145977341': ['B07YLS71PG', '193145977341', 'Kohls', 47.05, 'OR PRICE, ADD TO BAG'], '682510815864': ['B0781ZTCR8', '682510815864', 'Kohls', 22.2, '22.50'], '617847589959': ['B07NH46GPF', '617847589959', 'Kohls', 30.99, '24.00'], '194512568803': ['B07ZV3HX4S', '194512568803', 'Kohls', 32.25, 'OR PRICE, ADD TO BAG'], '192170513630': ['B07JNK38VL', '192170513630', 'Kohls', 27.9, '26.39'], '193150089381': ['B07WFJ5MLS', '193150089381', 'Kohls', 49.9, 'OR PRICE, ADD TO BAG'], '792850015302': ['B00XA7SAI4', '792850015302', 'Kohls', 37.9, '14.99'], '792850336995': ['B00LSC91CW', '792850336995', 'Kohls', 7.78, '8.99'], '764302224051': ['B07FNZG13J', '764302224051', 'Kohls', 9.79, '9.99'], '851877006455': ['B07XTVKCHR', '851877006455', 'Kohls', 9.99, '9.99'], '817810027116': ['B0769LK11D', '817810027116', 'Kohls', 9.99, '11.99'], '813277013754': ['B00IBLVWYS', '813277013754', 'Kohls', 'nan', '9.99'], '764302901402': ['B07SRFY91V', '764302901402', 'Kohls', 26.95, '9.99'], '792850019409': ['B077BHSHKP', '792850019409', 'Kohls', 15.08, '9.99']}
# Carter's List
# {'194133609664': ['B08G8VN5BS', '194133609664', 'Carters', 15.7, '14.00'], '194133569463': ['B08GBKDVYZ', '194133569463', 'Carters', 22.7, '20.00']}

#kohlsFinalList = [['B08K19Q9QM', '194573637616', 'Kohls', 16.48, '23.06'], ['B08K9CLJJK', '194133536472', 'Kohls', 24.99, '16.20'], ['B08G8VN5BS', '194133609664', 'Kohls', 13.99, '14.40'], ['B07FWL41RN', '191448503052', 'Kohls', 35.74, '39.99'], ['B07SBB4PJC', '191448445673', 'Kohls', 85.95, '29.99'], ['B082W63711', '194814415348', 'Kohls', 40.0, '34.99'], ['B0781ZTCR8', '682510815864', 'Kohls', 22.49, '30.00'], ['B07NH46GPF', '617847589959', 'Kohls', 48.01, '30.00'], ['B07JNK38VL', '192170513630', 'Kohls', 27.9, '24.74'], ['B07WFJ5MLS', '193150089381', 'Kohls', 49.9, '40.00'], ['B00XA7SAI4', '792850015302', 'Kohls', 38.03, '14.99'], ['B00OTE7QFA', '792850336995', 'Kohls', 7.46, '8.99'], ['B07FNZG13J', '764302224051', 'Kohls', 9.99, '9.99'], ['B07XTVKCHR', '851877006455', 'Kohls', 9.99, '9.99'], ['B0769LK11D', '817810027116', 'Kohls', 9.99, '11.99'], ['B000NC2MII', '792850336995', 'Kohls', 7.78, '8.99'], ['B07SRFY91V', '764302901402', 'Kohls', 26.89, '9.99'], ['B077BHSHKP', '792850019409', 'Kohls', 15.08, '9.99']]
#cartersFinalList = [['B08G8VN5BS', '194133609664', 'Carters', 15.7, '14.00'], ['B08GBKDVYZ', '194133569463', 'Carters', 22.7, '20.00']]