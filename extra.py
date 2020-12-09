"""
def findAsins(catids):
    for catid in catids:
        bestsellers = api.best_sellers_query(catid)

        for bestseller in bestsellers:
            asin = bestseller
            product = api.query(bestseller)
            upcList = product[0]['upcList']

            if(upcList != None):
                if asin not in rawAsinUpcDict:
                    rawAsinUpcDict[asin] = upcList
                else:
                    in_first = set(rawAsinUpcDict[asin])
                    in_second = set(upcList)

                    in_second_but_not_in_first = in_second - in_first

                    rawAsinUpcDict[asin].extend(list(in_second_but_not_in_first))

            print("Scraped ASIN: ", asin)
            print(rawAsinUpcDict)

    print("FINISHED SCRAPING AMAZON PRODUCTS")
"""

"""
URL = 'https://www.marshalls.com/us/store/shop/baby-clothes-accessories/_/N-4205482998?ln=2:1#/us/store/products/kids-toys-kids-toys-baby/_/N-4205482998?No=0&Nr=AND%28isEarlyAccess%3Afalse%2COR%28product.catalogId%3Atjmaxx%29%2Cproduct.siteId%3Amarshalls%29&&tag=va&va=true'
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')

itemDict = {}

for data in soup.find_all(class_="product-details equal-height-cell"):
    itemTitle = ""
    for title in data.find_all(class_="product-title"):
        itemTitle = title.text

    for price in data.find_all(class_="product-price"):
        value = price.text

        if price.find(class_='original-price'):
            price.find(class_='original-price').decompose()
            value = price.find(class_='discounted-price').text

        itemDict[itemTitle] = value.strip()

for item in itemDict:
    print(item, itemDict[item])
print(itemDict)
"""