from bs4 import BeautifulSoup
import requests

import time

#specific for myanimelist.net
class WebScraper():
    def __init__(self):
        pass

    def fetchPage(self, url):
        headers = {
            "accept" : "*/*",
            "accept-encoding" : "gzip, deflate, br, zstd",
            "accept-language" : "en-US,en;q=0.9",
            "user-agent": "Mozilla/5.0 : (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to fetch page: {response.status_code}")
        
    def getTitle(self, soup):
        titleTag = soup.find(itemprop="name")
        return titleTag.text if titleTag else 'No title'
    
    def getAltTitle(self, soup):
        leftsideTags = soup.find(class_="leftside")
        altTitleTags = leftsideTags.find_all(class_="spaceit_pad")
        for tag in altTitleTags:
            if "synonyms" in tag.contents[0].text.lower():
                return tag.text.replace("Synonyms:", "")
        return 'No alternative title'
    
    def getCreators(self, soup):
        leftsideTags = soup.find(class_="leftside")
        creator_tags = leftsideTags.find_all(class_="spaceit_pad")
        for tag in creator_tags:
            if "authors" in tag.get_text().lower():
                return tag.text.replace("Authors:", "").replace("\n", "")
        return 'No alternative title'
    
    def getSummary(self, soup):
        summary_tag = soup.find('span', itemprop='description')
        return summary_tag.text.strip() if summary_tag else 'No summary available'
    
    def gatherInfo(self, url):
        soup = BeautifulSoup(self.fetchPage(url), 'html.parser')
        output = f'Title: {self.getTitle(soup)}\nAlternative Titles: {self.getAltTitle(soup)}\nCreators: {self.getCreators(soup)}\nSummary: {self.getSummary(soup)}\n'
        return output
    
    def gatherManhwas(self):
        manhwaLinks =[]
        limit = 0
        while True:
            try:
                soup = BeautifulSoup(self.fetchPage(f'https://myanimelist.net/topmanga.php?type=manhwa&limit={limit}'), 'html.parser')
                manhwaTags = soup.find_all(class_="ranking-list")
                for manhwa in manhwaTags:
                    linkTag = manhwa.find(class_="hoverinfo_trigger fl-l ml12 mr8")
                    if linkTag and "href" in linkTag.attrs:
                        manhwaLinks.append(linkTag["href"])
                limit += 50
                time.sleep(1)
            except:
                break
        return manhwaLinks

        
scraper = WebScraper()
print(len(scraper.gatherManhwas()))