from bs4 import BeautifulSoup
import cloudscraper, time, random, json, threading, re
from concurrent.futures import ThreadPoolExecutor, as_completed

#specific for myanimelist.net
class WebScraper():
    
    detailFile = "manhwaDetails.jsonl"
    reviewFile = "manhwaReviews.jsonl"
    aliasFile = "alias.jsonl"
    userAgents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",

            # Chrome (Windows / Mac)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.199 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.616.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6090.0 Safari/537.36",

            # Edge (Chromium)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2145.59",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",

            # Firefox (Windows / Mac / Linux)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.6; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",

            # Safari (Mac / iPad)
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
            "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",

            # Opera
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/86.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/85.0.0.0",
        ]
    scraper = cloudscraper.create_scraper()
    linkDetailDict = {}
    linkReviewDict = {}
    fileLock = threading.Lock()

    def __init__(self):
        pass

    @classmethod
    def updateDetailDict(cls):
        dict = {}
        with open(cls.detailFile, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                dict[data["link"]] = data
        cls.linkDetailDict = dict

    @classmethod
    def updateReviewDict(cls):
        dict = {}
        with open(cls.reviewFile, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                dict[data["link"]] = data
        cls.linkReviewDict = dict
    

    @classmethod
    def getNewHeaders(cls):
        return {
            "User-Agent": random.choice(WebScraper.userAgents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }

    @classmethod
    def getPageHtml(cls, url):
        headers = WebScraper.getNewHeaders()
        for attempt in range(4):
            time.sleep(random.uniform(0.3, 2.5))
            response = WebScraper.scraper.get(url, headers=headers)
            if response.status_code == 200 and len(response.text) > 500:
                return response.text
            
            if attempt == 1:
                time.sleep(10)
                headers["User-Agent"] = random.choice(WebScraper.userAgents)
            
            WebScraper.scraper = cloudscraper.create_scraper()  # Refresh scraper on failure
        
        raise Exception(f"Failed to fetch page: {url} Code: {response.status_code}")

    @classmethod
    def writeToFile1(cls, file, details):
        with cls.fileLock:
            with open(file, "a", encoding="utf-8") as f: #probably some efficency issue with constanly opening but shouldnt matter much
                json.dump(details, f, ensure_ascii=False)
                f.write("\n")


#get details
    @classmethod
    def getDetails(cls, link):
        detailDict = cls.linkDetailDict
        if detailDict.get(link):
            return detailDict[link]

        success = False
        attempt = 0
        while not success and attempt < 3:
            soup = BeautifulSoup(WebScraper.getPageHtml(link), 'html.parser')
            
            if(soup.find(itemprop="name") and soup.find(class_="leftside") and soup.find('span', itemprop='description')): #ensure page is contains the correct content
                success = True
            elif attempt == 3:
                raise Exception(f'Cant reach{link}')
            else:
                attempt+=1
                print(f'failed at {link}, retrying in 10 seconds')
                time.sleep(10)
            
        #title
        titleText= cls.getTitleFromSoup(soup)


        leftsideTags = soup.find(class_="leftside")

        #alt titles
        altTitle = cls.getAltTitleFromSoup(soup)

        #authors
        creators = ""
        creator_tags = leftsideTags.find_all(class_="spaceit_pad")
        for tag in creator_tags:
            if "authors" in tag.get_text().lower():
                creators = re.sub(r'\s+', ' ', tag.text).replace("Authors:", "")
                break
        if not creators:
            creators = "no authors"
        

        #summary
        summary = ""
        summary_tag = soup.find('span', itemprop='description')
        summary = re.sub(r'\s+', ' ', summary_tag.text).strip()
        if not summary:
            summary = "no summary"

        #collect
        details = {"title": titleText, "alt_title": altTitle,"creators": creators ,"summary": summary}
        finalDict = {"link": link, "details": details}
        cls.writeToFile1(cls.detailFile, finalDict)
        
        return finalDict

    @classmethod 
    def getTitleFromSoup(cls, soup):
        titleTag = soup.find(itemprop="name") #no need to check if exist due to above if else block
        titleText = titleTag.find(string=True, recursive=False)
        name = re.sub(r'\s+', ' ', titleText).strip()
        return name

    @classmethod
    def getAltTitleFromSoup(cls, soup):
        leftsideTags = soup.find(class_="leftside")
        altTitleTags = leftsideTags.find_all(class_="spaceit_pad")
        alias = ""
        for tag in altTitleTags:
            if "synonyms" in tag.contents[0].text.lower():
                alias = re.sub(r'\s+', ' ', tag.text).strip().replace("Synonyms:", "")
                break
        if not alias:
            alias = "no alt title"
        
        return alias
    

#get reviews
    @classmethod
    def getReviews(cls, link):
        reviewDict = cls.linkReviewDict
        if reviewDict.get(link):
            return reviewDict[link]

        success = False
        attempt = 0
        while not success and attempt < 3:
            soup = BeautifulSoup(WebScraper.getPageHtml(link), 'html.parser')
            
            allReviewlinkTag = soup.find(class_="manga-info-review__header mal-navbar")
            if(allReviewlinkTag): #ensure page is contains the correct content
                success = True
                allReviewlink = allReviewlinkTag.find(class_="right").find("a")["href"] + "?spoiler=on"
            elif attempt == 3:
                raise Exception(f'Cant reach {link} reviews')
            else:
                attempt+=1
                print(f'failed at {link} review fetching, retrying in 10 seconds')
                time.sleep(10)
        
        result = {"link": link, "reviews": (cls.fetchReviews(allReviewlink, []))}
        cls.writeToFile1(cls.reviewFile, result)

        return(result)
    
    @classmethod
    def fetchReviews(cls, link, reviews):
        success = False
        attempt = 0
        while not success and attempt < 3:
            soup = BeautifulSoup(cls.getPageHtml(link), 'html.parser')
            reviewTags = soup.find_all(class_="review-element js-review-element")
            if(reviewTags): #ensure page is contains the correct content
                success = True
            elif attempt == 3:
                raise Exception(f'Cant reach {link} reviews')
            else:
                attempt+=1
                print(f'failed at {link} review fetching, retrying in 10 seconds')
                time.sleep(10)

        for review in reviewTags:
            try:
                content = review.find(class_="text").text.strip()
                if content:
                    content = re.sub(r'\s+', ' ', content)
                else:
                    continue
                score = review.find(class_="rating mt20 mb20 js-hidden").find(class_="num").text.strip()

                reviews.append({"score": score, "content": content})
            except Exception as e:
                print(e)
                continue
        
        linksAtEnd = soup.find(class_="ml4 mb8")
        nextPageLink = None
        if linksAtEnd:
            for link in linksAtEnd.find_all("a"):
                if link["data-ga-click-type"] == "review-more-reviews":
                    nextPageLink = link["href"]
                    break

        if nextPageLink:
            return cls.fetchReviews2(nextPageLink, reviews)
        return reviews


#getting details
    @classmethod
    def scrapeManhwaData(cls, upToLimit):

        for limit in range(0, upToLimit, 50): #up to 6400

            links = []
            try:
                manhwaTags = cls.getManhwaLinksForLimit(limit)

                for manhwa in manhwaTags:
                    linkTag = manhwa.find(class_="hoverinfo_trigger fl-l ml12 mr8")
                    if linkTag and "href" in linkTag.attrs:
                        link = linkTag["href"]
                        if link:
                            links.append(link)
    
            except Exception as e:
                print(f"Error fetching at limit {limit}: {e}")

            with ThreadPoolExecutor(max_workers=1) as executor: #turned off parallel 
                futures = {executor.submit(cls.scrapeReviewAndDetails, link): link for link in links}
                
                for future in as_completed(futures):
                    link = futures[future]
                    try:
                        result = future.result()
                        print(f"Completed: {link}")
                    except Exception as e:
                        print(f"Error scraping {link}: {e}")
                
    @classmethod
    def scrapeReviewAndDetails(cls, link):
        cls.getDetails(link)
        cls.getReviews(link)

    @classmethod
    def getManhwaLinksForLimit(cls, limit):
        success = False
        attempt = 0
        while not success and attempt < 3:
            soup = BeautifulSoup(cls.getPageHtml(f'https://myanimelist.net/topmanga.php?type=manhwa&limit={limit}'), 'html.parser')
            manhwaTags = soup.find_all(class_="ranking-list")
            if(manhwaTags): 
                 success = True
            elif attempt == 3:
                raise Exception(f'Cant reach limit:{limit}')
            else:
                attempt+=1
                print(f'failed at {limit} data fetching, retrying in 10 seconds')
                time.sleep(10)
        return manhwaTags

#getting alias
    @classmethod
    def getManhwaAlias(cls):
        doneLinks = []

        with open("alias.jsonl", "a", encoding="utf-8") as f:
            for limit in range(0, 100, 50): #up to 6400
                try:
                    manhwaTags = cls.getManhwaLinksForLimit(limit)

                    for manhwa in manhwaTags:
                        linkTag = manhwa.find(class_="hoverinfo_trigger fl-l ml12 mr8")
                        if linkTag and "href" in linkTag.attrs:
                            link = linkTag["href"]
                            if link and link not in doneLinks:
                                print(linkTag["href"])
                                aliasList = cls.scrapeAlias(linkTag["href"].strip())
                                result = {"link":linkTag["href"].strip(), "names": aliasList}

                                json.dump(result, f, ensure_ascii=False)
                                f.write("\n")
                                f.flush()
                except Exception as e:
                    print(f"Error fetching at limit {limit}: {e}")

    @classmethod
    def scrapeAlias(cls, link):
        try:
            success = False
            attempt = 0
            while not success and attempt < 3:
                soup = BeautifulSoup(cls.getPageHtml(link), 'html.parser')
                if(soup.find(class_="leftside")):
                    success = True
                else:
                    attempt+=1
                    print(f'failed at {link}, retrying in 10 seconds')
                    time.sleep(10)
            
            if success:
                #title
                name = cls.getTitleFromSoup(soup)

                #alt titles
                altTitle = cls.getAltTitleFromSoup(soup)

                #assume manhwa has a title
                if altTitle.lower() != "no alt title":
                    name = name + ", " + altTitle
                return[i.strip().lower() for i in name.split(",")]
            else:
                return "failed"
        except Exception as e:
            raise e


WebScraper.updateDetailDict()
WebScraper.updateReviewDict()


if __name__ == "__main__":
    print("running")

    WebScraper.getManhwaAlias()

    print("finished")